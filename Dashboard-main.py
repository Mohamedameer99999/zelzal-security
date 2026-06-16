import os, sys, json, sqlite3, datetime, hashlib, hmac, secrets, threading, webbrowser
from flask import Flask, render_template, request, jsonify, session, redirect

app = Flask(__name__)
app.secret_key = secrets.token_hex(32)
if getattr(sys, 'frozen', False):
    BASE_DIR = os.path.dirname(sys.executable)
else:
    BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_DIR = os.getenv("DASHBOARD_DB_DIR") or os.path.join(BASE_DIR, "Database")
DB = os.path.join(DB_DIR, "customers.db")
os.makedirs(DB_DIR, exist_ok=True)
SECRET_KEY = "Z3lzYWxTZWN1cml0eTIwMjU="

def get_db():
    conn = sqlite3.connect(DB)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_db()
    conn.executescript("""
        CREATE TABLE IF NOT EXISTS customers (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT, phone TEXT, product TEXT, period TEXT,
            license_key TEXT UNIQUE, mac_address TEXT,
            created_at TEXT, expires_at TEXT, active INTEGER DEFAULT 1,
            payment_date TEXT, notes TEXT
        );
        CREATE TABLE IF NOT EXISTS admins (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE, password TEXT
        );
        CREATE TABLE IF NOT EXISTS downloads (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            product TEXT, ip TEXT, user_agent TEXT, downloaded_at TEXT
        );
    """)
    # Default admin
    existing = conn.execute("SELECT id FROM admins WHERE username='admin'").fetchone()
    if not existing:
        pw = hashlib.sha256("admin123".encode()).hexdigest()
        conn.execute("INSERT INTO admins (username, password) VALUES (?,?)", ("admin", pw))
    conn.commit()
    conn.close()

PRODUCT_PREFIXES = {
    "cybershield": "CYBERSHIELD",
    "netguard": "NETGUARD",
    "filevault": "FILEVAULT",
    "wifiinspector": "WIFIINSPECTOR",
    "usbguardian": "USBGUARDIAN",
    "systemcleaner": "SYSTEMCLEANER",
    "duplicatefinder": "DUPLICATEFINDER",
    "fileshredder": "FILESHREDDER",
    "both": "BOTH",
}

def gen_license(product="cybershield", days=30):
    prefix = PRODUCT_PREFIXES.get(product, "CYBERSHIELD")
    rand = secrets.token_hex(10).upper()
    key_part = "-".join(rand[i:i+5] for i in range(0, 20, 5))
    expiry = (datetime.datetime.now() + datetime.timedelta(days=days)).strftime("%Y%m%d")
    payload = key_part + expiry
    sig = hmac.new(SECRET_KEY.encode(), payload.encode(), hashlib.sha256).hexdigest()[:8].upper()
    return f"{prefix}-{key_part}-{expiry}-{sig}"

def login_required(f):
    from functools import wraps
    @wraps(f)
    def wrapper(*a, **kw):
        if "admin" not in session:
            return redirect("/login")
        return f(*a, **kw)
    return wrapper

@app.route("/")
@login_required
def dashboard():
    conn = get_db()
    total = conn.execute("SELECT COUNT(*) FROM customers").fetchone()[0]
    active = conn.execute("SELECT COUNT(*) FROM customers WHERE active=1").fetchone()[0]
    expired = conn.execute("SELECT COUNT(*) FROM customers WHERE expires_at < datetime('now') AND active=1").fetchone()[0]
    monthly = conn.execute("SELECT COUNT(*) FROM customers WHERE period='شهري'").fetchone()[0]
    yearly = conn.execute("SELECT COUNT(*) FROM customers WHERE period='سنوي'").fetchone()[0]
    conn.close()
    return render_template("dashboard.html", total=total, active=active, expired=expired, monthly=monthly, yearly=yearly)

@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form["username"]
        password = hashlib.sha256(request.form["password"].encode()).hexdigest()
        conn = get_db()
        row = conn.execute("SELECT id FROM admins WHERE username=? AND password=?", (username, password)).fetchone()
        conn.close()
        if row:
            session["admin"] = username
            return redirect("/")
        return render_template("login.html", error="خطأ في اسم المستخدم أو كلمة المرور")
    return render_template("login.html")

@app.route("/admin/change-password", methods=["POST"])
@login_required
def change_password():
    old = hashlib.sha256(request.form["old_password"].encode()).hexdigest()
    new = request.form["new_password"].strip()
    if len(new) < 6:
        return render_template("dashboard.html", error="كلمة السر الجديدة يجب أن تكون 6 أحرف على الأقل")
    conn = get_db()
    row = conn.execute("SELECT id FROM admins WHERE username=? AND password=?", (session["admin"], old)).fetchone()
    if not row:
        conn.close()
        return render_template("dashboard.html", error="كلمة السر القديمة غير صحيحة")
    pw = hashlib.sha256(new.encode()).hexdigest()
    conn.execute("UPDATE admins SET password=? WHERE username=?", (pw, session["admin"]))
    conn.commit()
    conn.close()
    return render_template("dashboard.html", success="✅ تم تغيير كلمة السر بنجاح")

@app.route("/logout")
def logout():
    session.pop("admin", None)
    return redirect("/login")

@app.route("/customers")
@login_required
def customers():
    conn = get_db()
    rows = conn.execute("SELECT * FROM customers ORDER BY id DESC").fetchall()
    conn.close()
    return render_template("customers.html", customers=rows)

@app.route("/api/customers")
@login_required
def api_customers():
    conn = get_db()
    rows = conn.execute("SELECT * FROM customers ORDER BY id DESC").fetchall()
    conn.close()
    return jsonify([dict(r) for r in rows])

@app.route("/api/customers/add", methods=["POST"])
@login_required
def add_customer():
    data = request.json
    name = data.get("name", "").strip()
    phone = data.get("phone", "").strip()
    product = data.get("product", "cybershield")
    period = data.get("period", "شهري")
    days = 30 if period == "شهري" else 365
    notes = data.get("notes", "")
    license_key = gen_license(product, days)
    expires = (datetime.datetime.now() + datetime.timedelta(days=days)).isoformat()
    conn = get_db()
    conn.execute("""INSERT INTO customers (name,phone,product,period,license_key,created_at,expires_at,active,payment_date,notes)
        VALUES (?,?,?,?,?,?,?,1,?,?)""",
        (name, phone, product, period, license_key, datetime.datetime.now().isoformat(), expires,
         datetime.datetime.now().strftime("%Y-%m-%d"), notes))
    conn.commit()
    conn.close()
    return jsonify({"success": True, "license_key": license_key})

@app.route("/api/customers/delete/<int:id>", methods=["POST"])
@login_required
def delete_customer(id):
    conn = get_db()
    conn.execute("DELETE FROM customers WHERE id=?", (id,))
    conn.commit()
    conn.close()
    return jsonify({"success": True})

@app.route("/api/customers/toggle/<int:id>", methods=["POST"])
@login_required
def toggle_customer(id):
    conn = get_db()
    row = conn.execute("SELECT active FROM customers WHERE id=?", (id,)).fetchone()
    if row:
        new = 0 if row[0] else 1
        conn.execute("UPDATE customers SET active=? WHERE id=?", (new, id))
        conn.commit()
    conn.close()
    return jsonify({"success": True})

@app.route("/api/license/generate", methods=["POST"])
@login_required
def generate_license():
    data = request.json
    product = data.get("product", "cybershield")
    days = int(data.get("days", 30))
    key = gen_license(product, days)
    return jsonify({"license_key": key, "expires": (datetime.datetime.now() + datetime.timedelta(days=days)).isoformat()})

@app.route("/api/stats")
@login_required
def stats():
    conn = get_db()
    monthly = conn.execute("""SELECT SUM(CASE
        WHEN product='both' AND period='شهري' THEN 500
        WHEN product='netguard' AND period='شهري' THEN 250
        WHEN product='wifiinspector' AND period='شهري' THEN 150
        WHEN product='filevault' AND period='شهري' THEN 100
        WHEN product='usbguardian' AND period='شهري' THEN 100
        WHEN product='systemcleaner' AND period='شهري' THEN 100
        WHEN product='duplicatefinder' AND period='شهري' THEN 80
        WHEN product='fileshredder' AND period='شهري' THEN 120
        WHEN period='شهري' THEN 200 ELSE 0 END) FROM customers WHERE active=1""").fetchone()[0] or 0
    yearly = conn.execute("""SELECT SUM(CASE
        WHEN product='both' AND period='سنوي' THEN 4500
        WHEN product='netguard' AND period='سنوي' THEN 3000
        WHEN product='wifiinspector' AND period='سنوي' THEN 1200
        WHEN product='filevault' AND period='سنوي' THEN 800
        WHEN product='usbguardian' AND period='سنوي' THEN 800
        WHEN product='systemcleaner' AND period='سنوي' THEN 600
        WHEN product='duplicatefinder' AND period='سنوي' THEN 480
        WHEN product='fileshredder' AND period='سنوي' THEN 720
        WHEN period='سنوي' THEN 2000 ELSE 0 END) FROM customers WHERE active=1""").fetchone()[0] or 0
    conn.close()
    return jsonify({"monthly": monthly, "yearly": yearly, "total": monthly + yearly})

@app.route("/verify-license")
def verify_license():
    key = request.args.get("key", "")
    conn = get_db()
    row = conn.execute("SELECT * FROM customers WHERE license_key=?", (key,)).fetchone()
    conn.close()
    if row:
        return jsonify({
            "valid": bool(row["active"]),
            "product": row["product"],
            "status": "نشط" if row["active"] else "غير نشط",
            "expiry": row["expires_at"][:10] if row["expires_at"] else "غير محدد",
            "customer": row["name"]
        })
    return jsonify({"valid": False, "message": "مفتاح غير موجود في قاعدة البيانات"})

@app.route("/api/download/track", methods=["POST"])
def track_download():
    data = request.json or {}
    conn = get_db()
    conn.execute("INSERT INTO downloads (product, ip, user_agent, downloaded_at) VALUES (?,?,?,?)",
        (data.get("product", "unknown"), request.remote_addr, request.headers.get("User-Agent", ""),
         datetime.datetime.now().isoformat()))
    conn.commit()
    conn.close()
    return jsonify({"ok": True})

@app.route("/api/download/stats")
@login_required
def download_stats():
    conn = get_db()
    total = conn.execute("SELECT COUNT(*) FROM downloads").fetchone()[0]
    by_product = conn.execute("SELECT product, COUNT(*) as cnt FROM downloads GROUP BY product ORDER BY cnt DESC").fetchall()
    today = datetime.datetime.now().strftime("%Y-%m-%d")
    today_dl = conn.execute("SELECT COUNT(*) FROM downloads WHERE downloaded_at LIKE ?", (f"{today}%",)).fetchone()[0]
    conn.close()
    return jsonify({"total": total, "today": today_dl, "by_product": [dict(r) for r in by_product]})

init_db()

if __name__ == "__main__":
    port = int(os.getenv("PORT", 8080))
    try: webbrowser.open(f"http://localhost:{port}")
    except: pass
    print(f"\n== Customer Dashboard: http://localhost:{port} ==")
    print(f"   Username: admin | Password: admin123")
    app.run(host="0.0.0.0", port=port, debug=False)
