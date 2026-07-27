#!/usr/bin/env python
"""Kurulum öncesinde config.json hazırlayan script."""
import json
import sys

try:
    sys.path.insert(0, '.')
    from common.settings import DEFAULT_SETTINGS
    
    config = {
        'database_name': DEFAULT_SETTINGS.get('database_name', 'yazarkasa'),
        'dealer_code': 'BAYI-001',
        'dealer_name': 'Bayi',
        'theme': 'light',
        'font_scale': 1.0,
        'terminal_mode': DEFAULT_SETTINGS.get('terminal_mode', 'ingenico'),
        'terminal_host': DEFAULT_SETTINGS.get('terminal_host', '192.168.1.100'),
        'terminal_tcp_port': DEFAULT_SETTINGS.get('terminal_tcp_port', 6240),
        'terminal_baud': DEFAULT_SETTINGS.get('terminal_baud', 9600),
    }
    
    with open('config.json', 'w', encoding='utf-8') as f:
        json.dump(config, f, indent=2, ensure_ascii=False)
    
    print('[OK] config.json hazirlandi')
    sys.exit(0)
    
except Exception as e:
    print(f'[HATA] config.json olusturulamadi: {e}', file=sys.stderr)
    sys.exit(1)
