import os
tools = ['Wi-Fi-Inspector','File-Vault','USB-Guardian','System-Cleaner','Duplicate-Finder','File-Shredder']
base = r'F:\zelzal prog-AI'
for t in tools:
    path = os.path.join(base, t, 'tool.py')
    content = open(path, encoding='utf-8').read()
    status = 'OK' if 'app = Flask' in content else 'ISSUE'
    print(f'{t}: {status}')