#!/usr/bin/env python3
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
from web.server import start_server
from core.arp_detector import ARPDetector

if __name__ == '__main__':
    print('===========================================')
    print('   CYBER SHIELD v5.0.0')
    print('   Security Platform')
    print('===========================================')
    print()
    arp_detector = ARPDetector()
    start_server(arp_detector)
