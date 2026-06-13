import sys
from pathlib import Path

if getattr(sys, 'frozen', False):
    ROOT = Path(sys._MEIPASS)
    DATA = Path(sys.executable).resolve().parent / 'data'
else:
    ROOT = Path(__file__).resolve().parent.parent
    DATA = ROOT / 'data'

DATA.mkdir(parents=True, exist_ok=True)

def get_data_dir():
    return str(DATA)
