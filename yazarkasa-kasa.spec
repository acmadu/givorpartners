# -*- mode: python ; coding: utf-8 -*-
from PyInstaller.utils.hooks import collect_all, collect_submodules

datas = [
    ('common', 'common'),
    ('pos', 'pos'),
    ('assets', 'assets'),
    ('config.json.example', '.'),  # config.json.example bundled; rename to config.json on first run
    ('version.py', '.'),
]
binaries = []
hiddenimports = [
    'pymongo', 'pymongo.auth', 'pymongo.auth_oidc',
    'bson', 'PyQt5', 'PyQt5.QtChart', 'PyQt5.sip',
    'openpyxl',
    'dns', 'dns.resolver', 'dns.rdtypes', 'dns.asyncresolver',
]
hiddenimports += collect_submodules('pymongo')
hiddenimports += collect_submodules('dns')
tmp_ret = collect_all('PyQt5')
datas += tmp_ret[0]; binaries += tmp_ret[1]; hiddenimports += tmp_ret[2]
tmp_chart = collect_all('PyQt5.QtChart')
datas += tmp_chart[0]; binaries += tmp_chart[1]; hiddenimports += tmp_chart[2]


a = Analysis(
    ['start_pos.py'],
    pathex=['.'],
    binaries=binaries,
    datas=datas,
    hiddenimports=hiddenimports,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=['tkinter', 'matplotlib', 'numpy', 'scipy'],
    noarchive=False,
    optimize=1,
)
pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.datas,
    [],
    name='yazarkasa-kasa',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    # icon='assets/kasa.ico',  # Windows/macOS icon — eklemek istersen
)
