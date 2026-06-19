#!/usr/bin/env python3
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
from web.server import start_server

if __name__ == '__main__':
    print('===========================================')
    print('   NetGuard Monitor v1.1.0')
    print('   Network Monitor System')
    print('===========================================')
    print()
    start_server()
