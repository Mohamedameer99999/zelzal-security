import subprocess, re, socket, threading
from datetime import datetime

_ARP_CACHE = {}
_lock = threading.Lock()

def _parse_subnet(subnet):
    m = re.match(r'(\d+\.\d+\.\d+)', subnet)
    return m.group(1) if m else '192.168.1'

def _run_arp():
    try:
        r = subprocess.run(['arp', '-a'], capture_output=True, text=True, timeout=5)
        devices = []
        for line in r.stdout.split('\n'):
            m = re.search(r'(\d+\.\d+\.\d+\.\d+)\s+([a-f0-9\-]{17})', line, re.I)
            if m:
                ip = m.group(1)
                mac = m.group(2).replace('-', ':')
                devices.append({'ip': ip, 'mac': mac, 'hostname': '', 'vendor': _guess_vendor(mac)})
                with _lock:
                    _ARP_CACHE[ip] = {'mac': mac, 'seen': datetime.now()}
        return devices
    except:
        return []

def _guess_vendor(mac):
    vendors = {
        '00:50:56': 'VMware', '00:0c:29': 'VMware', '00:05:69': 'VMware',
        '08:00:27': 'Oracle VB', '00:15:5d': 'Hyper-V',
        '00:1a:11': 'Cisco', '00:1a:a1': 'Cisco',
        '00:1b:17': 'Intel', '00:1f:29': 'Intel',
        '00:1e:68': 'Dell', '00:21:5a': 'HP', '00:23:7d': 'HP',
        '00:24:21': 'Samsung', '00:25:56': 'Apple', '00:26:bb': 'Apple',
        '30:10:e4': 'Huawei', '58:69:6c': 'Xiaomi',
        '64:70:02': 'TP-Link', 'c0:4a:00': 'TP-Link',
        '38:83:45': 'Realtek', '10:05:ca': 'Netgear', '00:1b:2f': 'Linksys',
    }
    prefix = mac[:8].upper()
    if prefix in vendors:
        return vendors[prefix]
    return 'Unknown'

def _ping_sweep(subnet_prefix):
    found = []
    def _ping(ip):
        try:
            r = subprocess.run(['ping', '-n', '1', '-w', '200', ip], capture_output=True, text=True, timeout=2)
            if 'TTL=' in r.stdout or 'Reply from' in r.stdout:
                found.append(ip)
        except:
            pass
    threads = []
    for i in range(1, 255):
        t = threading.Thread(target=_ping, args=(f'{subnet_prefix}.{i}',))
        t.start()
        threads.append(t)
    for t in threads:
        t.join(timeout=3)
    return found

def discover(subnet='192.168.1.0/24'):
    prefix = _parse_subnet(subnet)
    devices = _run_arp()
    if devices:
        return devices
    found_ips = _ping_sweep(prefix)
    return [{'ip': ip, 'mac': '', 'hostname': '', 'vendor': ''} for ip in found_ips]

def get_gateway():
    try:
        r = subprocess.run(['ipconfig'], capture_output=True, text=True, timeout=5)
        m = re.search(r'Default Gateway[ .]+:\s+(\d+\.\d+\.\d+\.\d+)', r.stdout)
        if m:
            return m.group(1)
    except:
        pass
    return '192.168.1.1'

def get_subnet(gateway):
    parts = gateway.split('.')
    return f'{parts[0]}.{parts[1]}.{parts[2]}'
