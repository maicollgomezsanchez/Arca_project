# -*- mode: python ; coding: utf-8 -*-


a = Analysis(
    ['escalestri.py'],
    pathex=[],
    binaries=[],
    datas=[('vista.kv', 'vista.kv')],
    hiddenimports=[
    'gpiozero',
    'gpiozero.pins.rpigpio',
    'gpiozero.pins.pigpio',
    'gpiozero.pins.native',
    'gpiozero.pins.lgpio',
    'RPi.GPIO'
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    noarchive=False,
    optimize=0,
)
pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.datas,
    [],
    name='escalestri',
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
)
