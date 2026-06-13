import sqlite3, threading, time
from datetime import datetime
from . import paths

_local = threading.local()

def _get_conn():
    if not hasattr(_local, 'conn') or _local.conn is None:
        _local.conn = sqlite3.connect(str(paths.DATA / 'cybershield.db'), check_same_thread=False)
        _local.conn.execute("PRAGMA journal_mode=WAL")
        _local.conn.execute("PRAGMA foreign_keys=ON")
    return _local.conn

def init_db():
    conn = _get_conn()
    conn.executescript("""
        CREATE TABLE IF NOT EXISTS alerts (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            type TEXT, message TEXT, severity TEXT DEFAULT 'info',
            source TEXT DEFAULT '', acknowledged INTEGER DEFAULT 0,
            timestamp TEXT DEFAULT (datetime('now','localtime'))
        );
        CREATE TABLE IF NOT EXISTS events (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            event_type TEXT, detail TEXT, data TEXT,
            timestamp TEXT DEFAULT (datetime('now','localtime'))
        );
        CREATE TABLE IF NOT EXISTS devices (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            ip TEXT, mac TEXT, hostname TEXT, vendor TEXT DEFAULT '',
            first_seen TEXT DEFAULT (datetime('now','localtime')),
            last_seen TEXT DEFAULT (datetime('now','localtime')),
            status TEXT DEFAULT 'online'
        );
        CREATE TABLE IF NOT EXISTS scan_log (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            scan_type TEXT, result_count INTEGER DEFAULT 0,
            timestamp TEXT DEFAULT (datetime('now','localtime'))
        );
    """)
    conn.commit()

def add_alert(alert_type, message, severity='info', source=''):
    conn = _get_conn()
    conn.execute("INSERT INTO alerts (type,message,severity,source) VALUES (?,?,?,?)",
                 (alert_type, message, severity, source))
    conn.commit()
    return conn.execute("SELECT last_insert_rowid()").fetchone()[0]

def get_alerts(limit=50):
    conn = _get_conn()
    rows = conn.execute("SELECT id,type,message,severity,source,acknowledged,timestamp FROM alerts ORDER BY id DESC LIMIT ?", (limit,))
    return [dict(r) for r in [dict(zip([d[0] for d in rows.description], row)) for row in rows.fetchall()]]

def log_event(event_type, detail, data=None):
    conn = _get_conn()
    conn.execute("INSERT INTO events (event_type,detail,data) VALUES (?,?,?)",
                 (event_type, detail, str(data or '')))
    conn.commit()

def add_device(ip, mac='', hostname='', vendor=''):
    conn = _get_conn()
    existing = conn.execute("SELECT id FROM devices WHERE ip=? AND mac=?", (ip, mac)).fetchone()
    if existing:
        conn.execute("UPDATE devices SET last_seen=datetime('now','localtime'), status='online', hostname=?, vendor=? WHERE id=?",
                     (hostname, vendor, existing[0]))
    else:
        conn.execute("INSERT INTO devices (ip,mac,hostname,vendor) VALUES (?,?,?,?)",
                     (ip, mac, hostname, vendor))
    conn.commit()

def get_devices():
    conn = _get_conn()
    rows = conn.execute("SELECT id,ip,mac,hostname,vendor,first_seen,last_seen,status FROM devices ORDER BY last_seen DESC").fetchall()
    return [dict(zip([d[0] for d in conn.execute("PRAGMA table_info(devices)").fetchall()], row)) for row in rows]

def log_scan(scan_type, count):
    conn = _get_conn()
    conn.execute("INSERT INTO scan_log (scan_type,result_count) VALUES (?,?)", (scan_type, count))
    conn.commit()

def get_stats():
    conn = _get_conn()
    total_alerts = conn.execute("SELECT COUNT(*) FROM alerts").fetchone()[0]
    unread = conn.execute("SELECT COUNT(*) FROM alerts WHERE acknowledged=0").fetchone()[0]
    last_scan = conn.execute("SELECT timestamp FROM scan_log ORDER BY id DESC LIMIT 1").fetchone()
    return {
        'total_alerts': total_alerts,
        'unread_alerts': unread,
        'last_scan': last_scan[0] if last_scan else '-',
    }
