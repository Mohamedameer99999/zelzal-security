import os, hashlib, re, threading
from datetime import datetime
from . import database as db

SUSPICIOUS_EXTS = {'.exe', '.dll', '.scr', '.bat', '.vbs', '.ps1', '.jar', '.js', '.vba', '.docm', '.xlsm'}
SUSPICIOUS_PATTERNS = [
    (b'CreateRemoteThread', 'API Injection'),
    (b'WriteProcessMemory', 'Memory Injection'),
    (b'VirtualAllocEx', 'Memory Allocation'),
    (b'URLDownloadToFile', 'Download Exec'),
    (b'WinExec', 'Process Execution'),
    (b'cmd.exe /c', 'Command Execution'),
    (b'powershell -', 'PowerShell'),
    (b'[EncryptedOutputStream]', 'Encryption'),
]

KNOWN_MALWARE_HASHES = set()

def get_file_hash(path):
    try:
        h = hashlib.sha256()
        with open(path, 'rb') as f:
            for chunk in iter(lambda: f.read(65536), b''):
                h.update(chunk)
        return h.hexdigest()
    except:
        return ''

def scan_file(path, quick=True):
    result = {'path': path, 'threats': [], 'clean': True, 'hash': ''}
    try:
        if not os.path.isfile(path):
            return result
        size = os.path.getsize(path)
        if quick and size > 10 * 1024 * 1024:
            result['note'] = 'Skipped (large file)'
            return result
        result['hash'] = get_file_hash(path)
        if result['hash'] in KNOWN_MALWARE_HASHES:
            result['threats'].append('Known malware hash')
            result['clean'] = False
        if size < 50 * 1024 * 1024:
            ext = os.path.splitext(path)[1].lower()
            if ext in SUSPICIOUS_EXTS:
                with open(path, 'rb', errors='ignore') as f:
                    content = f.read(min(size, 1024 * 1024))
                    for pattern, desc in SUSPICIOUS_PATTERNS:
                        if pattern in content:
                            result['threats'].append(desc)
                            result['clean'] = False
    except:
        pass
    return result

def scan_directory(path, recursive=False, max_files=100):
    results = []
    count = 0
    try:
        for root, dirs, files in os.walk(path):
            for f in files:
                if count >= max_files:
                    break
                fp = os.path.join(root, f)
                r = scan_file(fp)
                if not r['clean'] or r.get('threats'):
                    results.append(r)
                    db.add_alert('malware', f'تهديد: {r["threats"][0]} في {f}', 'critical', 'AntiVirus')
                count += 1
            if not recursive:
                break
    except:
        pass
    return results
