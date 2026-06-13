import subprocess, re, json, time, threading
from collections import defaultdict

class ARPDetector:
    def __init__(self):
        self._known_ips = {}
        self._alerts = []
        self._running = False
        self._thread = None

    def _get_arp_table(self):
        try:
            result = subprocess.run(["arp", "-a"], capture_output=True, text=True, creationflags=subprocess.CREATE_NO_WINDOW)
            entries = []
            for line in result.stdout.split('\n'):
                parts = re.split(r'\s+', line.strip())
                if len(parts) >= 3 and re.match(r'\d+\.\d+\.\d+\.\d+', parts[0]):
                    entries.append({"ip": parts[0], "mac": parts[1], "type": parts[2] if len(parts) > 2 else "dynamic"})
            return entries
        except:
            return []

    def check_arp_spoof(self):
        entries = self._get_arp_table()
        ip_macs = defaultdict(set)
        alerts = []
        for e in entries:
            ip_macs[e["ip"]].add(e["mac"])

        for ip, macs in ip_macs.items():
            if len(macs) > 1:
                alerts.append({"ip": ip, "macs": list(macs), "type": "ARP Spoofing محتمل"})
                self._alerts.append({"ip": ip, "macs": list(macs), "time": time.strftime("%H:%M:%S"), "type": "ARP Spoofing"})
        return alerts

    def start_monitoring(self, interval=30):
        self._running = True
        def _loop():
            while self._running:
                self.check_arp_spoof()
                time.sleep(interval)
        self._thread = threading.Thread(target=_loop, daemon=True)
        self._thread.start()

    def stop_monitoring(self):
        self._running = False

    def get_alerts(self):
        return self._alerts[-50:]
