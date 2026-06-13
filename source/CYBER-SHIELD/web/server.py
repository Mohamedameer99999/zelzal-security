import json, os, sys, secrets, time
from http.server import HTTPServer, SimpleHTTPRequestHandler
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from core import config, monitor, scanner, firewall, antivirus, usb_control, keylogger, database as db, license as lic, wifi_scanner
from core.arp_detector import ARPDetector

config.load()
PORT = config.get('port')
PASSWORD = config.get('admin_password')

if getattr(sys, 'frozen', False):
    FRONTEND_DIR = Path(sys._MEIPASS) / 'web' / 'frontend'
else:
    FRONTEND_DIR = Path(__file__).resolve().parent / 'frontend'

_sessions = {}
_arp = None

def _make_session():
    token = secrets.token_hex(32)
    _sessions[token] = time.time() + 86400
    return token

def _check_session(token):
    if not token or not PASSWORD:
        return not bool(PASSWORD)
    expiry = _sessions.get(token, 0)
    if expiry < time.time():
        _sessions.pop(token, None)
        return False
    return True

class ShieldHandler(SimpleHTTPRequestHandler):
    def _get_cookie(self, name):
        raw = self.headers.get('Cookie', '') or ''
        for c in raw.split(';'):
            c = c.strip()
            if c.startswith(name + '='):
                return c[len(name)+1:]
        return None

    def _is_auth(self):
        if not PASSWORD:
            return True
        return _check_session(self._get_cookie('session'))

    def do_GET(self):
        if not self._is_auth() and self.path != '/login' and self.path != '/api/login':
            self.send_response(302)
            self.send_header('Location', '/login')
            self.end_headers()
            return
        if self.path == '/login':
            self._serve('login.html')
        elif self.path == '/':
            self._serve('index.html')
        elif self.path.startswith('/css/') or self.path.startswith('/js/'):
            self._serve(self.path.lstrip('/'))
        elif self.path == '/api/status':
            self._json(monitor.get_status())
        elif self.path == '/api/scan/network':
            devs = scanner.scan_network()
            for d in devs:
                db.add_device(d['ip'], d.get('mac',''), d.get('hostname',''), d.get('vendor',''))
            self._json({'devices': devs, 'count': len(devs)})
        elif self.path.startswith('/api/scan/ports/'):
            ip = self.path.split('/')[-1]
            self._json({'ip': ip, 'ports': scanner.scan_ports(ip)})
        elif self.path == '/api/connections':
            self._json(firewall.get_active_connections())
        elif self.path == '/api/ids':
            self._json(firewall.ids_scan())
        elif self.path == '/api/antivirus/scan':
            dirs = [os.environ.get('TEMP', 'C:\\'), os.path.expanduser('~\\Downloads')]
            all_results = []
            for d in dirs:
                all_results.extend(antivirus.scan_directory(d))
            self._json({'scanned': True, 'threats': len(all_results), 'results': all_results})
        elif self.path == '/api/usb':
            self._json(usb_control.scan_usb())
        elif self.path == '/api/keylogger':
            self._json(keylogger.scan_processes())
        elif self.path == '/api/alerts':
            self._json(db.get_alerts(50))
        elif self.path == '/api/devices':
            self._json(db.get_devices())
        elif self.path == '/api/license/status':
            info = lic.get_license_info()
            if info:
                valid, msg = lic.validate_license(info['key'])
                self._json({'valid': valid, 'message': msg, 'info': info})
            else:
                self._json({'valid': False, 'message': 'لا يوجد ترخيص', 'info': None})
        elif self.path == '/api/wifi/scan':
            self._json({'networks': wifi_scanner.scan_wifi()})
        elif self.path == '/api/arp/check':
            alerts = _arp.get_alerts() if _arp else []
            spoof = _arp.check_arp_spoof() if _arp else []
            self._json({'alerts': alerts, 'spoof': spoof})
        else:
            self.send_response(404)
            self.end_headers()
            self.wfile.write(b'{"error":"not found"}')

    def do_POST(self):
        if self.path == '/api/login':
            try:
                content = self.rfile.read(int(self.headers.get('Content-Length', 0)))
                data = json.loads(content)
                if data.get('user') == config.get('admin_user') and data.get('password') == PASSWORD:
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
                from core.database import _get_conn
                _get_conn().execute("UPDATE alerts SET acknowledged=1 WHERE id=?", (data.get('id'),))
                _get_conn().commit()
                self._json({'success': True})
            except Exception as e:
                self._json({'error': str(e)}, 400)
        elif self.path == '/api/license/activate':
            try:
                content = self.rfile.read(int(self.headers.get('Content-Length', 0)))
                data = json.loads(content)
                key = data.get('key', '')
                import uuid
                mac = ':'.join(hex(uuid.getnode())[2:].zfill(12)[i:i+2] for i in range(0, 12, 2))
                valid, msg = lic.validate_license(key, mac)
                if valid:
                    self._json({'success': True, 'message': msg})
                else:
                    self._json({'success': False, 'error': msg}, 400)
            except Exception as e:
                self._json({'error': str(e)}, 400)
        elif self.path == '/api/arp/start':
            if _arp:
                _arp.start_monitoring()
                self._json({'success': True, 'message': 'تم بدء مراقبة ARP'})
            else:
                self._json({'error': 'ARP detector not initialized'}, 400)
        elif self.path == '/api/arp/stop':
            if _arp:
                _arp.stop_monitoring()
                self._json({'success': True, 'message': 'تم إيقاف مراقبة ARP'})
            else:
                self._json({'error': 'ARP detector not initialized'}, 400)
        else:
            self._json({'error': 'not found'}, 404)

    def _serve(self, name):
        fp = FRONTEND_DIR / name
        if not fp.exists():
            self.send_response(404)
            self.end_headers()
            return
        ext = fp.suffix.lower()
        types = {'.css':'text/css','.js':'application/javascript','.html':'text/html; charset=utf-8','.png':'image/png','.svg':'image/svg+xml'}
        self.send_response(200)
        self.send_header('Content-Type', types.get(ext, 'application/octet-stream'))
        self.end_headers()
        with open(fp, 'rb') as f:
            self.wfile.write(f.read())

    def _json(self, data, status=200):
        self.send_response(status)
        self.send_header('Content-Type', 'application/json')
        self.end_headers()
        self.wfile.write(json.dumps(data, ensure_ascii=False, default=str).encode())

    def log_message(self, format, *args):
        pass

def start_server(arp_detector=None):
    global _arp
    _arp = arp_detector
    monitor.start()
    if _arp:
        _arp.start_monitoring()
        print('[CYBER SHIELD] ARP monitoring started')
    server = HTTPServer(('0.0.0.0', PORT), ShieldHandler)
    print(f'[CYBER SHIELD] Running on http://localhost:{PORT}')
    if PASSWORD:
        print(f'[CYBER SHIELD] Authentication enabled')
    server.serve_forever()

if __name__ == '__main__':
    start_server()
