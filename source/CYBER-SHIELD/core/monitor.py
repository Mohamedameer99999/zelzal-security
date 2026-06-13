import time, threading
from datetime import datetime
from . import database as db
from . import scanner
from . import firewall
from . import antivirus
from . import usb_control
from . import keylogger
from . import config

_running = False
_threads = []

def _scan_loop():
    db.init_db()
    while _running:
        try:
            devices = scanner.scan_network()
            for d in devices:
                db.add_device(d['ip'], d.get('mac', ''), d.get('hostname', ''), d.get('vendor', ''))
            db.log_scan('network', len(devices))
        except Exception as e:
            db.add_alert('scan_error', f'Network scan: {str(e)}', 'critical', 'Monitor')
        time.sleep(max(10, int(config.get('scan_interval'))))

def _ids_loop():
    while _running:
        try:
            result = firewall.ids_scan()
        except:
            pass
        time.sleep(30)

def _usb_loop():
    while _running:
        try:
            usb_control.scan_usb()
        except:
            pass
        time.sleep(15)

def _kl_loop():
    while _running:
        try:
            keylogger.scan_processes()
        except:
            pass
        time.sleep(60)

def start():
    global _running, _threads
    if _running:
        return
    _running = True
    db.init_db()
    targets = [
        ('Scanner', _scan_loop),
        ('IDS', _ids_loop),
        ('USB', _usb_loop),
        ('Keylogger', _kl_loop),
    ]
    for name, target in targets:
        t = threading.Thread(target=target, daemon=True)
        t.start()
        _threads.append(t)

def stop():
    global _running
    _running = False

def get_status():
    return {
        'running': _running,
        'devices': len(scanner.scan_network()),
        'stats': db.get_stats(),
    }
