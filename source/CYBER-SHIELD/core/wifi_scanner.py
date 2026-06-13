import subprocess, re, json

def scan_wifi():
    try:
        result = subprocess.run(["netsh", "wlan", "show", "networks", "mode=Bssid"],
                              capture_output=True, text=True, creationflags=subprocess.CREATE_NO_WINDOW)
        output = result.stdout
        networks = []
        current = {}
        for line in output.split('\n'):
            line = line.strip()
            if line.startswith("SSID"):
                if current:
                    networks.append(current)
                current = {"ssid": line.split(":", 1)[1].strip() if ":" in line else ""}
            elif "BSSID" in line and ":" in line:
                current["bssid"] = line.split(":", 1)[1].strip()
            elif "Signal" in line and ":" in line:
                current["signal"] = line.split(":", 1)[1].strip()
            elif "Radio type" in line and ":" in line:
                current["radio"] = line.split(":", 1)[1].strip()
            elif "Channel" in line and ":" in line:
                current["channel"] = line.split(":", 1)[1].strip()
            elif "Authentication" in line and ":" in line:
                current["auth"] = line.split(":", 1)[1].strip()
            elif "Encryption" in line and ":" in line:
                current["encryption"] = line.split(":", 1)[1].strip()
        if current:
            networks.append(current)
        return networks
    except Exception as e:
        return [{"error": str(e)}]

def get_wifi_info_json():
    return json.dumps(scan_wifi(), ensure_ascii=False)
