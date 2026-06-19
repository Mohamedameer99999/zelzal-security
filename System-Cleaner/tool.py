import os, json
from flask import Flask, render_template, request, jsonify

app = Flask(__name__)
LICENSE_FILE = os.path.join(os.path.dirname(__file__), "license.txt")
TOOL_NAME = "System Cleaner"
TOOL_TAG = "تنظيف النظام"
TOOL_COLOR = "#ffd93d"

def load_license():
    if os.path.exists(LICENSE_FILE):
        with open(LICENSE_FILE) as f:
            return f.read().strip()
    return ""

def save_license(key):
    with open(LICENSE_FILE, "w") as f:
        f.write(key.strip())

def validate_key(key):
    parts = key.strip().split("-")
    if len(parts) != 4:
        return False
    if not all(len(p) == 4 and p.isalnum() for p in parts):
        return False
    if not key.startswith("SC"):
        return False
    return True

@app.route("/")
def index():
    licensed = load_license()
    if licensed and validate_key(licensed):
        return render_template("dashboard.html", tool_name=TOOL_NAME, tool_tag=TOOL_TAG, tool_color=TOOL_COLOR)
    return render_template("license.html", tool_name=TOOL_NAME, tool_tag=TOOL_TAG, tool_color=TOOL_COLOR)

@app.route("/", methods=["POST"])
def activate():
    key = request.form.get("license_key", "")
    if validate_key(key):
        save_license(key)
        return render_template("dashboard.html", tool_name=TOOL_NAME, tool_tag=TOOL_TAG, tool_color=TOOL_COLOR)
    return render_template("license.html", tool_name=TOOL_NAME, tool_tag=TOOL_TAG, tool_color=TOOL_COLOR, error="مفتاح الترخيص غير صالح")

@app.route("/dashboard")
def dashboard():
    licensed = load_license()
    if not licensed or not validate_key(licensed):
        return render_template("license.html", tool_name=TOOL_NAME, tool_tag=TOOL_TAG, tool_color=TOOL_COLOR, error="الرجاء تفعيل الترخيص أولاً")
    return render_template("dashboard.html", tool_name=TOOL_NAME, tool_tag=TOOL_TAG, tool_color=TOOL_COLOR)

@app.route("/api/clean", methods=["POST"])
def api_clean():
    licensed = load_license()
    if not licensed or not validate_key(licensed):
        return jsonify({"error": "غير مرخص"}), 403
    return jsonify({"cleaned": "2.4GB", "files_removed": 1287, "temp_cleared": True, "cache_cleared": True})

@app.route("/api/analyze")
def api_analyze():
    licensed = load_license()
    if not licensed or not validate_key(licensed):
        return jsonify({"error": "غير مرخص"}), 403
    return jsonify({"total_waste": "4.7GB", "temp_files": "1.2GB", "cache": "2.1GB", "logs": "0.8GB", "recycle": "0.6GB"})

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5104, debug=False)
