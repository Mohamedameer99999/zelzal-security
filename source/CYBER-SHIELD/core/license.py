import hashlib, hmac, secrets, sqlite3, datetime, json, os
from core.paths import get_data_dir

SECRET_KEY = "Z3lzYWxTZWN1cml0eTIwMjU="

def generate_license_key(product="cybershield", days=30):
    raw = secrets.token_hex(10).upper()
    key = "-".join(raw[i:i+5] for i in range(0, 20, 5))
    sig = hmac.new(SECRET_KEY.encode(), key.encode(), hashlib.sha256).hexdigest()[:8]
    full_key = f"{key}-{sig}"
    expiry = (datetime.datetime.now() + datetime.timedelta(days=days)).isoformat()
    db_path = os.path.join(get_data_dir(), "licenses.db")
    conn = sqlite3.connect(db_path)
    conn.execute("""CREATE TABLE IF NOT EXISTS licenses (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        license_key TEXT UNIQUE,
        mac_address TEXT,
        product TEXT,
        created_at TEXT,
        expires_at TEXT,
        active INTEGER DEFAULT 1
    )""")
    conn.execute("INSERT OR IGNORE INTO licenses (license_key, product, created_at, expires_at, active) VALUES (?,?,?,?,1)",
                 (full_key, product, datetime.datetime.now().isoformat(), expiry))
    conn.commit()
    conn.close()
    return full_key

def validate_license(license_key, mac_address=None):
    db_path = os.path.join(get_data_dir(), "licenses.db")
    if not os.path.exists(db_path):
        return False, "لا يوجد ترخيص"
    conn = sqlite3.connect(db_path)
    row = conn.execute("SELECT * FROM licenses WHERE license_key=? AND active=1", (license_key,)).fetchone()
    conn.close()
    if not row:
        return False, "مفتاح الترخيص غير صحيح"
    expires = datetime.datetime.fromisoformat(row[5])
    if datetime.datetime.now() > expires:
        return False, "انتهت صلاحية الترخيص"
    if row[2] and mac_address and row[2] != mac_address:
        return False, "الترخيص مرتبط بجهاز آخر"
    if not row[2] and mac_address:
        conn = sqlite3.connect(db_path)
        conn.execute("UPDATE licenses SET mac_address=? WHERE license_key=?", (mac_address, license_key))
        conn.commit()
        conn.close()
    return True, f"ساري حتى {expires.strftime('%Y-%m-%d')}"

def get_license_info():
    db_path = os.path.join(get_data_dir(), "licenses.db")
    if not os.path.exists(db_path):
        return None
    conn = sqlite3.connect(db_path)
    row = conn.execute("SELECT * FROM licenses WHERE active=1 ORDER BY id DESC LIMIT 1").fetchone()
    conn.close()
    if row:
        return {"key": row[1], "mac": row[2], "product": row[3], "created": row[4], "expires": row[5], "active": row[6]}
    return None
