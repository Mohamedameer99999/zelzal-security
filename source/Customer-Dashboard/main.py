import os, json, sqlite3, datetime, hashlib, hmac, secrets, threading, webbrowser
from flask import Flask, render_template, request, jsonify, session, redirect

app = Flask(__name__)
app.secret_key = secrets.token_hex(32)
DB_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "Database")
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
    """)
    # Default admin
    existing = conn.execute("SELECT id FROM admins WHERE username='admin'").fetchone()
    if not existing:
        pw = hashlib.sha256("admin123".encode()).hexdigest()
        conn.execute("INSERT INTO admins (username, password) VALUES (?,?)", ("admin", pw))
    conn.commit()
    conn.close()

def gen_license(product="cybershield", days=30):
    rand = secrets.token_hex(10).upper()
    key_part = "-".join(rand[i:i+5] for i in range(0, 20, 5))
    expiry = (datetime.datetime.now() + datetime.timedelta(days=days)).strftime("%Y%m%d")
    payload = key_part + expiry
    sig = hmac.new(SECRET_KEY.encode(), payload.encode(), hashlib.sha256).hexdigest()[:8].upper()
    return f"{key_part}-{expiry}-{sig}"

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
    monthly = conn.execute("SELECT SUM(CASE WHEN product='both' AND period='شهري' THEN 500 WHEN product='netguard' AND period='شهري' THEN 250 WHEN period='شهري' THEN 200 ELSE 0 END) FROM customers WHERE active=1").fetchone()[0] or 0
    yearly = conn.execute("SELECT SUM(CASE WHEN product='both' AND period='سنوي' THEN 4500 WHEN product='netguard' AND period='سنوي' THEN 3000 WHEN period='سنوي' THEN 2000 ELSE 0 END) FROM customers WHERE active=1").fetchone()[0] or 0
    conn.close()
    return jsonify({"monthly": monthly, "yearly": yearly, "total": monthly + yearly})

if __name__ == "__main__":
    init_db()
    port = 8080
    webbrowser.open(f"http://localhost:{port}")
    print(f"\n== Customer Dashboard: http://localhost:{port} ==")
    print(f"   Username: admin | Password: admin123")
    app.run(host="0.0.0.0", port=port, debug=False)
