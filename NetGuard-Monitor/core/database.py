import sqlite3, threading, json
from datetime import datetime
from .paths import get_db_path

_db_local = threading.local()

def _get_conn():
    if not hasattr(_db_local, 'conn') or _db_local.conn is None:
        _db_local.conn = sqlite3.connect(str(get_db_path()), check_same_thread=False)
        _db_local.conn.row_factory = sqlite3.Row
        _db_local.conn.execute("PRAGMA journal_mode=WAL")
    return _db_local.conn

def init_db():
    c = _get_conn()
    c.executescript("""
        CREATE TABLE IF NOT EXISTS devices (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            ip TEXT NOT NULL,
            mac TEXT,
            hostname TEXT DEFAULT '',
            vendor TEXT DEFAULT '',
            first_seen TEXT NOT NULL,
            last_seen TEXT NOT NULL,
            status TEXT DEFAULT 'online',
            UNIQUE(ip)
        );
        CREATE TABLE IF NOT EXISTS bandwidth_log (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            device_ip TEXT,
            timestamp TEXT NOT NULL,
            bytes_sent INTEGER DEFAULT 0,
            bytes_recv INTEGER DEFAULT 0
        );
        CREATE TABLE IF NOT EXISTS alerts (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            type TEXT NOT NULL,
            message TEXT NOT NULL,
            severity TEXT DEFAULT 'info',
            timestamp TEXT NOT NULL,
            acknowledged INTEGER DEFAULT 0
        );
        CREATE TABLE IF NOT EXISTS network_stats (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp TEXT NOT NULL,
            total_devices INTEGER DEFAULT 0,
            online_devices INTEGER DEFAULT 0,
            total_bytes_sent INTEGER DEFAULT 0,
            total_bytes_recv INTEGER DEFAULT 0
        );
    """)
    c.commit()

def add_device(ip, mac='', hostname='', vendor=''):
    now = datetime.now().isoformat()
    c = _get_conn()
    row = c.execute("SELECT id FROM devices WHERE ip=?", (ip,)).fetchone()
    if row:
        c.execute("UPDATE devices SET last_seen=?, status='online', hostname=COALESCE(NULLIF(?,''), hostname) WHERE ip=?", (now, hostname, ip))
    else:
        c.execute("INSERT INTO devices (ip, mac, hostname, vendor, first_seen, last_seen) VALUES (?,?,?,?,?,?)", (ip, mac, hostname, vendor, now, now))
    c.commit()

def mark_device_offline(ip):
    c = _get_conn()
    c.execute("UPDATE devices SET status='offline' WHERE ip=?", (ip,))
    c.commit()

def get_devices():
    c = _get_conn()
    return [dict(r) for r in c.execute("SELECT * FROM devices ORDER BY last_seen DESC")]

def log_bandwidth(device_ip, sent, recv):
    now = datetime.now().isoformat()
    c = _get_conn()
    c.execute("INSERT INTO bandwidth_log (device_ip, timestamp, bytes_sent, bytes_recv) VALUES (?,?,?,?)", (device_ip, now, sent, recv))
    c.commit()

def add_alert(alert_type, message, severity='info'):
    now = datetime.now().isoformat()
    c = _get_conn()
    c.execute("INSERT INTO alerts (type, message, severity, timestamp) VALUES (?,?,?,?)", (alert_type, message, severity, now))
    c.commit()
    return dict(c.execute("SELECT * FROM alerts WHERE id=last_insert_rowid()").fetchone())

def get_alerts(limit=20):
    c = _get_conn()
    return [dict(r) for r in c.execute("SELECT * FROM alerts ORDER BY timestamp DESC LIMIT ?", (limit,))]

def log_network_stats(total, online, sent, recv):
    now = datetime.now().isoformat()
    c = _get_conn()
    c.execute("INSERT INTO network_stats (timestamp, total_devices, online_devices, total_bytes_sent, total_bytes_recv) VALUES (?,?,?,?,?)", (now, total, online, sent, recv))
    c.commit()

def get_network_history(hours=24):
    from datetime import datetime, timedelta
    since = (datetime.now() - timedelta(hours=hours)).isoformat()
    c = _get_conn()
    return [dict(r) for r in c.execute("SELECT * FROM network_stats WHERE timestamp >= ? ORDER BY timestamp ASC", (since,))]

def get_bandwidth_history(hours=24):
    from datetime import datetime, timedelta
    since = (datetime.now() - timedelta(hours=hours)).isoformat()
    c = _get_conn()
    return [dict(r) for r in c.execute("SELECT * FROM bandwidth_log WHERE timestamp >= ? ORDER BY timestamp ASC", (since,))]

def get_stats():
    c = _get_conn()
    total = c.execute("SELECT COUNT(*) as c FROM devices").fetchone()['c']
    online = c.execute("SELECT COUNT(*) as c FROM devices WHERE status='online'").fetchone()['c']
    alerts = c.execute("SELECT COUNT(*) as c FROM alerts WHERE acknowledged=0").fetchone()['c']
    last_scan = c.execute("SELECT MAX(timestamp) as t FROM network_stats").fetchone()['t'] or '-'
    return {'total_devices': total, 'online_devices': online, 'unread_alerts': alerts, 'last_scan': last_scan}
