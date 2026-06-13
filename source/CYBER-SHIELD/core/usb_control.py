import subprocess, re, threading, time
from datetime import datetime
from . import database as db

_known_usbs = {}
_lock = threading.Lock()
_blocked = False
_allowed_vids = set()

def list_usb_devices():
    try:
        r = subprocess.run(['wmic', 'path', 'Win32_USBControllerDevice', 'get', 'Dependent'],
                           capture_output=True, text=True, timeout=5)
        devices = []
        for line in r.stdout.split('\n'):
            m = re.search(r'DeviceID="([^"]+)".*VID_([0-9A-F]{4})', line, re.I)
            if m:
                vid = m.group(2)
                devices.append({'vid': vid, 'device_id': m.group(1)})
        return devices
    except:
        return []

def get_drives():
    try:
        r = subprocess.run(['wmic', 'logicaldisk', 'get', 'DeviceID,DriveType,VolumeName'],
                           capture_output=True, text=True, timeout=5)
        drives = []
        for line in r.stdout.split('\n'):
            parts = line.strip().split()
            if len(parts) >= 2 and parts[1] == '2':
                name = parts[2] if len(parts) > 2 else ''
                drives.append({'drive': parts[0], 'name': name})
        return drives
    except:
        return []

def scan_usb():
    devices = list_usb_devices()
    drives = get_drives()
    with _lock:
        for d in devices:
            vid = d['vid']
            if vid not in _known_usbs:
                _known_usbs[vid] = {'first_seen': datetime.now().isoformat(), 'count': 1}
                if _blocked and vid not in _allowed_vids:
                    db.add_alert('usb_blocked', f'USB محظور: VID_{vid}', 'warning', 'USB')
                else:
                    db.add_alert('usb_new', f'USB جديد: VID_{vid}', 'info', 'USB')
            else:
                _known_usbs[vid]['count'] += 1
    return {'devices': devices, 'drives': drives, 'known': len(_known_usbs), 'blocked': _blocked}
