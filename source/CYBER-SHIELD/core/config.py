import json, os, sys
from pathlib import Path

if getattr(sys, 'frozen', False):
    CONFIG_DIR = Path(sys.executable).resolve().parent
else:
    CONFIG_DIR = Path(__file__).resolve().parent.parent

CONFIG_PATH = CONFIG_DIR / 'config.json'

DEFAULTS = {
    'port': 9090,
    'admin_user': 'admin',
    'admin_password': '',
    'scan_interval': 60,
    'interface': '0.0.0.0',
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
