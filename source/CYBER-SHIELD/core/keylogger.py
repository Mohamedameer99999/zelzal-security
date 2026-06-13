import subprocess, re, threading, time
from datetime import datetime
from . import database as db

KEYLOGGER_PROCESSES = ['keylogger', 'keylog', 'logkeys', 'pykeylogger', 'refog', 'actualkeylogger',
                       'spyrix', 'kidlogger', 'elitekeylogger', 'mspy', 'flexispy']
KEYLOGGER_FILES = ['keylogger.exe', 'keylog.exe', 'logkeys.exe', 'hook.dll', 'keyhook.dll']

def scan_processes():
    try:
        r = subprocess.run(['tasklist', '/FO', 'CSV', '/NH'], capture_output=True, text=True, timeout=5)
        threats = []
        for line in r.stdout.split('\n'):
            parts = line.strip().strip('"').split('","')
            if len(parts) >= 1:
                name = parts[0].lower()
                for kl in KEYLOGGER_PROCESSES:
                    if kl in name:
                        threats.append({'name': parts[0], 'type': 'process', 'threat': f'Keylogger: {name}'})
        for t in threats:
            db.add_alert('keylogger', t['threat'], 'critical', 'Keylogger')
        return {'scanned': True, 'threats': threats}
    except:
        return {'scanned': False, 'threats': []}

def scan_startup():
    try:
        r = subprocess.run(['wmic', 'startup', 'get', 'caption,command'],
                           capture_output=True, text=True, timeout=5)
        threats = []
        for line in r.stdout.split('\n'):
            line_lower = line.lower()
            for kl in KEYLOGGER_FILES:
                if kl in line_lower:
                    threats.append({'startup': line.strip(), 'threat': f'Keylogger في بدء التشغيل: {kl}'})
        for t in threats:
            db.add_alert('keylogger_startup', t['threat'], 'critical', 'Keylogger')
        return threats
    except:
        return []
