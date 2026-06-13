import subprocess, re, socket, threading, ipaddress
from datetime import datetime

VENDORS = {
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

def guess_vendor(mac):
    return VENDORS.get(mac[:8].upper(), 'Unknown')

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

def arp_scan():
    try:
        r = subprocess.run(['arp', '-a'], capture_output=True, text=True, timeout=5)
        devices = []
        for line in r.stdout.split('\n'):
            m = re.search(r'(\d+\.\d+\.\d+\.\d+)\s+([a-f0-9\-]{17})', line, re.I)
            if m:
                ip = m.group(1)
                mac = m.group(2).replace('-', ':')
                try:
                    hostname = socket.gethostbyaddr(ip)[0]
                except:
                    hostname = ''
                devices.append({'ip': ip, 'mac': mac, 'hostname': hostname, 'vendor': guess_vendor(mac)})
        return devices
    except:
        return []

def ping_sweep(subnet_prefix=None):
    if not subnet_prefix:
        subnet_prefix = get_subnet(get_gateway())
    found = []
    def _ping(ip):
        try:
            r = subprocess.run(['ping', '-n', '1', '-w', '150', ip], capture_output=True, text=True, timeout=2)
            if 'TTL=' in r.stdout:
                found.append(ip)
        except:
            pass
    threads = []
    for i in range(1, 255):
        t = threading.Thread(target=_ping, args=(f'{subnet_prefix}.{i}',))
        t.start()
        threads.append(t)
    for t in threads:
        t.join(timeout=2)
    return found

def scan_network():
    devices = arp_scan()
    if not devices:
        ips = ping_sweep()
        devices = [{'ip': ip, 'mac': '', 'hostname': '', 'vendor': ''} for ip in ips]
    return devices

def scan_ports(ip, ports=None):
    if not ports:
        ports = [21,22,23,25,53,80,110,135,139,143,443,445,993,995,1433,1521,2049,3306,3389,5432,5900,6379,8080,8443,9090,9091,27017]
    open_ports = []
    def _check(p):
        try:
            s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            s.settimeout(0.5)
            if s.connect_ex((ip, p)) == 0:
                try:
                    service = socket.getservbyport(p)
                except:
                    service = ''
                open_ports.append({'port': p, 'service': service, 'state': 'open'})
            s.close()
        except:
            pass
    threads = []
    for p in ports:
        t = threading.Thread(target=_check, args=(p,))
        t.start()
        threads.append(t)
    for t in threads:
        t.join(timeout=1)
    return sorted(open_ports, key=lambda x: x['port'])
