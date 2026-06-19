import os, json
from flask import Flask, render_template, request, jsonify

app = Flask(__name__)
LICENSE_FILE = os.path.join(os.path.dirname(__file__), "license.txt")
TOOL_NAME = "Wi-Fi Inspector"
TOOL_TAG = "تحليل الشبكات اللاسلكية"
TOOL_COLOR = "#00f5a0"

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
    if not key.startswith("WF"):
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

@app.route("/api/scan", methods=["POST"])
def api_scan():
    licensed = load_license()
    if not licensed or not validate_key(licensed):
        return jsonify({"error": "غير مرخص"}), 403
    data = request.get_json() or {}
    target = data.get("target", "192.168.1.0/24")
    results = [
        {"ssid": "ZELZAL_5G", "bssid": "AA:BB:CC:DD:EE:01", "signal": -45, "channel": 6, "encryption": "WPA2", "vendor": "ZELZAL"},
        {"ssid": "ZELZAL_Guest", "bssid": "AA:BB:CC:DD:EE:02", "signal": -62, "channel": 11, "encryption": "WPA2", "vendor": "ZELZAL"},
        {"ssid": "Neighbor_WiFi", "bssid": "AA:BB:CC:DD:EE:03", "signal": -78, "channel": 1, "encryption": "WPA3", "vendor": "TP-Link"},
        {"ssid": "Cafe_Free", "bssid": "AA:BB:CC:DD:EE:04", "signal": -85, "channel": 6, "encryption": "Open", "vendor": "Unknown"},
    ]
    return jsonify({"networks": results, "count": len(results), "target": target})

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5101, debug=False)
