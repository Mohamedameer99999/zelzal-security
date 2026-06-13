import subprocess, re, socket, threading, time
from datetime import datetime
from . import database as db

_active_connections = []
_blocked_ips = set()
_lock = threading.Lock()

def get_connections():
    try:
        r = subprocess.run(['netstat', '-n'], capture_output=True, text=True, timeout=5)
        connections = []
        for line in r.stdout.split('\n'):
            m = re.search(r'TCP\s+(\S+)\s+(\S+)\s+(\S+)', line)
            if m:
                local = m.group(1)
                remote = m.group(2)
                state = m.group(3)
                if remote != '*:*' and state != 'LISTENING':
                    connections.append({'local': local, 'remote': remote, 'state': state})
        return connections
    except:
        return []

def get_firewall_rules():
    try:
        r = subprocess.run(['netsh', 'advfirewall', 'firewall', 'show', 'rule', 'name=all'],
                           capture_output=True, text=True, timeout=10)
        rules = []
        name = ''
        for line in r.stdout.split('\n'):
            nm = re.match(r'Rule Name:\s+(.+)', line)
            if nm:
                if name:
                    rules.append({'name': name.strip()})
                name = nm.group(1)
        if name:
            rules.append({'name': name.strip()})
        return rules
    except:
        return []

def detect_suspicious(connections):
    suspicious = []
    suspicious_ports = {445, 3389, 22, 23, 1433, 3306, 5900, 6379, 27017}
    for c in connections:
        remote = c['remote']
        if ':' in remote:
            ip_part = remote.rsplit(':', 1)[0]
            port_part = int(remote.rsplit(':', 1)[1])
            if port_part in suspicious_ports and c['state'] == 'ESTABLISHED':
                if not ip_part.startswith(('127.', '192.168.', '10.', '172.16.')):
                    suspicious.append({'ip': ip_part, 'port': port_part, 'service': c['local'], 'state': c['state']})
        elif remote != '*:*':
            suspicious.append({'ip': remote, 'port': 0, 'service': c['local'], 'state': c['state']})
    return suspicious

def ids_scan():
    conns = get_connections()
    susp = detect_suspicious(conns)
    for s in susp:
        db.add_alert('suspicious_connection', f'اتصال مشبوه: {s["ip"]}:{s["port"]} ({s["state"]})', 'warning', 'IDS')
    return {'total_connections': len(conns), 'suspicious': len(susp), 'connections': conns[:100], 'suspicious_list': susp}

def get_active_connections():
    return get_connections()[:100]
