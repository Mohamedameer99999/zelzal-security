import json, os, sys
from pathlib import Path

if getattr(sys, 'frozen', False):
    CONFIG_DIR = Path(sys.executable).resolve().parent
else:
    CONFIG_DIR = Path(__file__).resolve().parent.parent

CONFIG_PATH = CONFIG_DIR / 'config.json'

DEFAULTS = {
    'port': 9091,
    'scan_interval': 30,
    'subnet': '192.168.1.0/24',
    'admin_user': 'admin',
    'admin_password': '',
    'notify_whatsapp': False,
    'whatsapp_webhook': '',
}

_config = None

def load():
    global _config
    if CONFIG_PATH.exists():
        with open(CONFIG_PATH, 'r', encoding='utf-8') as f:
            data = json.load(f)
        _config = {**DEFAULTS, **data}
    else:
        _config = dict(DEFAULTS)
    return _config

def get(key):
    global _config
    if _config is None:
        load()
    return _config.get(key, DEFAULTS.get(key))

def save(data):
    global _config
    _config = {**DEFAULTS, **(_config or {}), **data}
    with open(CONFIG_PATH, 'w', encoding='utf-8') as f:
        json.dump(_config, f, ensure_ascii=False, indent=2)
