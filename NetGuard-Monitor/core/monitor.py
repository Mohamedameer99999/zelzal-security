import time, threading, socket, urllib.request, urllib.parse
from datetime import datetime
from . import database as db
from . import detector
from . import bandwidth
from . import config

_running = False
_thread = None

def _scan_network():
    gateway = detector.get_gateway()
    subnet = config.get('subnet')
    new_devices = detector.discover(subnet)
    for d in new_devices:
        try:
            hostname = socket.gethostbyaddr(d['ip'])[0] if d['ip'] else ''
        except:
            hostname = ''
        db.add_device(d['ip'], d.get('mac', ''), hostname, d.get('vendor', ''))
    prev_devices = {r['ip'] for r in db.get_devices() if r['status'] == 'online'}
    current_ips = {d['ip'] for d in new_devices}
    for ip in prev_devices - current_ips:
        if ip != gateway:
            db.mark_device_offline(ip)
    for d in new_devices:
        if d['ip'] not in prev_devices and d['ip'] != gateway:
            msg = f'جهاز جديد: {d["ip"]} ({d.get("vendor","Unknown")})'
            alert = db.add_alert('new_device', msg, 'warning')
            _notify_whatsapp(msg)
            return alert
    return None

def _notify_whatsapp(message):
    try:
        if not config.get('notify_whatsapp'):
            return
        webhook = config.get('whatsapp_webhook')
        if webhook:
            data = urllib.parse.urlencode({'message': message, 'source': 'NetGuard'}).encode()
            urllib.request.urlopen(webhook, data=data, timeout=5)
    except:
        pass

def _loop():
    global _running
    db.init_db()
    bandwidth.start_monitoring()
    gateway = detector.get_gateway()
    while _running:
        try:
            alert = _scan_network()
            all_dev = db.get_devices()
            online = [d for d in all_dev if d['status'] == 'online']
            bw = bandwidth.get_bandwidth()
            db.log_network_stats(len(all_dev), len(online), bw['total_sent'], bw['total_recv'])
        except Exception as e:
            db.add_alert('error', f'Scan error: {str(e)}', 'critical')
        time.sleep(max(5, int(config.get('scan_interval'))))

def start():
    global _running, _thread
    if _running:
        return
    _running = True
    _thread = threading.Thread(target=_loop, daemon=True)
    _thread.start()

def stop():
    global _running
    _running = False

def get_status():
    return {
        'running': _running,
        'interval': config.get('scan_interval'),
        'gateway': detector.get_gateway(),
        'scans': db.get_stats(),
        'bandwidth': bandwidth.get_bandwidth(),
    }

def get_devices():
    return db.get_devices()

def get_alerts(limit=20):
    return db.get_alerts(limit)

def get_network_history(hours=6):
    return db.get_network_history(hours)

def get_bandwidth_history():
    return bandwidth.get_history(30)
