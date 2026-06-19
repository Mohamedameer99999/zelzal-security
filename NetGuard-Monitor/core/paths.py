import sys, os
from pathlib import Path

def get_project_root():
    if getattr(sys, 'frozen', False):
        return Path(sys._MEIPASS)
    return Path(__file__).resolve().parent.parent

def get_data_dir():
    if getattr(sys, 'frozen', False):
        return Path(sys.executable).parent / 'data'
    return get_project_root() / 'data'

def get_db_path():
    d = get_data_dir()
    d.mkdir(parents=True, exist_ok=True)
    return d / 'netguard.db'
