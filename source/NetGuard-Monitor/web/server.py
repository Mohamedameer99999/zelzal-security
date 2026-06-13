import json, os, sys, threading, hashlib, hmac, secrets, time
from http.server import HTTPServer, SimpleHTTPRequestHandler
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from core import monitor
from core import config
from core.license import validate_license, get_license_info
from core.arp_detector import ARPDetector

config.load()
PORT = config.get('port')

if getattr(sys, 'frozen', False):
    FRONTEND_DIR = Path(sys._MEIPASS) / 'web' / 'frontend'
else:
    FRONTEND_DIR = Path(__file__).resolve().parent / 'frontend'

PASSWORD = config.get('admin_password')
_sessions = {}

def _make_session():
    token = secrets.token_hex(32)
    _sessions[token] = time.time() + 86400
    return token

def _check_session(token):
    if not token:
        return False
    expiry = _sessions.get(token, 0)
    if expiry < time.time():
        _sessions.pop(token, None)
        return False
    return True

def _needs_auth():
    return bool(PASSWORD)

class NetGuardHandler(SimpleHTTPRequestHandler):

    def _is_authenticated(self):
        if not _needs_auth():
            return True
        token = self._get_cookie('session')
        return _check_session(token)

    def _get_cookie(self, name):
        raw = self.headers.get('Cookie', '')
        for c in raw.split(';'):
            c = c.strip()
            if c.startswith(name + '='):
                return c[len(name)+1:]
        return None

    def _set_cookie(self, name, value, max_age=86400):
        self.send_header('Set-Cookie', f'{name}={value}; Path=/; Max-Age={max_age}; HttpOnly; SameSite=Lax')

    def do_GET(self):
        if self.path == '/login' or (self.path == '/' and not self._is_authenticated()):
            self._serve_file('login.html')
        elif self.path == '/api/login':
            self._serve_file('login.html')
        elif self.path == '/' and _needs_auth() and not self._is_authenticated():
            self.send_response(302)
            self.send_header('Location', '/login')
            self.end_headers()
        elif self.path == '/':
            self._serve_file('index.html')
        elif self.path.startswith('/css/') or self.path.startswith('/js/'):
            self._serve_file(self.path.lstrip('/'))
        elif self.path == '/api/status':
            self._json(monitor.get_status())
        elif self.path == '/api/devices':
            self._json(monitor.get_devices())
        elif self.path == '/api/alerts':
            self._json(monitor.get_alerts(20))
        elif self.path == '/api/network-history':
            self._json(monitor.get_network_history(6))
        elif self.path == '/api/bandwidth':
            self._json(monitor.get_bandwidth_history())
        elif self.path == '/api/license/status':
            info = get_license_info()
            if info:
                valid, msg = validate_license(info['key'])
                self._json({'valid': valid, 'info': info, 'message': msg})
            else:
                self._json({'valid': False, 'info': None, 'message': 'لا يوجد ترخيص'})
        elif self.path == '/api/arp/check':
            if hasattr(self.server, 'arp_detector') and self.server.arp_detector:
                self._json(self.server.arp_detector.get_alerts())
            else:
                self._json([])
        else:
            self.send_response(404)
            self.end_headers()
            self.wfile.write(b'{"error":"not found"}')

    def do_POST(self):
        if self.path == '/api/login':
            try:
                content = self.rfile.read(int(self.headers.get('Content-Length', 0)))
                data = json.loads(content)
                user = data.get('user', '')
                pw = data.get('password', '')
                if user == config.get('admin_user') and pw == PASSWORD:
                    token = _make_session()
                    self._json({'success': True, 'token': token})
                else:
                    self._json({'error': 'بيانات دخول غير صحيحة'}, 401)
            except Exception as e:
                self._json({'error': str(e)}, 400)
        elif self.path == '/api/ack-alert':
            try:
                content = self.rfile.read(int(self.headers.get('Content-Length', 0)))
                data = json.loads(content)
                alert_id = data.get('id')
                from core.database import _get_conn
                _get_conn().execute("UPDATE alerts SET acknowledged=1 WHERE id=?", (alert_id,))
                _get_conn().commit()
                self._json({'success': True})
            except Exception as e:
                self._json({'error': str(e)}, 400)
        elif self.path == '/api/license/activate':
            try:
                content = self.rfile.read(int(self.headers.get('Content-Length', 0)))
                data = json.loads(content)
                key = data.get('key', '')
                valid, msg = validate_license(key)
                self._json({'success': valid, 'message': msg})
            except Exception as e:
                self._json({'error': str(e)}, 400)
        elif self.path == '/api/arp/start':
            if hasattr(self.server, 'arp_detector') and self.server.arp_detector:
                self.server.arp_detector.start_monitoring()
                self._json({'success': True, 'message': 'ARP monitoring started'})
            else:
                self._json({'error': 'ARP detector not available'}, 400)
        elif self.path == '/api/arp/stop':
            if hasattr(self.server, 'arp_detector') and self.server.arp_detector:
                self.server.arp_detector.stop_monitoring()
                self._json({'success': True, 'message': 'ARP monitoring stopped'})
            else:
                self._json({'error': 'ARP detector not available'}, 400)
        else:
            self._json({'error':'not found'}, 404)

    def _serve_file(self, name):
        fp = FRONTEND_DIR / name
        if not fp.exists() or not fp.is_file():
            self.send_response(404)
            self.end_headers()
            return
        ext = fp.suffix.lower()
        types = {'.css':'text/css','.js':'application/javascript','.html':'text/html; charset=utf-8','.png':'image/png','.svg':'image/svg+xml'}
        self.send_response(200)
        self.send_header('Content-Type', types.get(ext, 'application/octet-stream'))
        self.send_header('Access-Control-Allow-Origin', '*')
        self.end_headers()
        with open(fp, 'rb') as f:
            self.wfile.write(f.read())

    def _json(self, data, status=200):
        self.send_response(status)
        self.send_header('Content-Type', 'application/json')
        self.send_header('Access-Control-Allow-Origin', '*')
        self.end_headers()
        self.wfile.write(json.dumps(data, ensure_ascii=False, default=str).encode())

    def log_message(self, format, *args):
        pass

def start_server(arp_detector=None):
    monitor.start()
    server = HTTPServer(('0.0.0.0', PORT), NetGuardHandler)
    server.arp_detector = arp_detector
    if _needs_auth():
        print(f'[NetGuard] Authentication enabled (user: {config.get("admin_user")})')
    else:
        print(f'[NetGuard] No authentication (set admin_password in config.json)')
    print(f'[NetGuard] Monitor running on http://localhost:{PORT}')
    server.serve_forever()

if __name__ == '__main__':
    start_server()
