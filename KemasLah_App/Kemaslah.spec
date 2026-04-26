# -*- mode: python ; coding: utf-8 -*-

a = Analysis(
    ['main.py'],
    pathex=[],
    binaries=[],
    # 1. DATAS: This maps every custom folder in your screenshot into the .exe
    datas=[
        ('AI', 'AI'),
        ('assets', 'assets'),
        ('auth', 'auth'),
        ('models', 'models'),
        ('src', 'src')
    ],
    # 2. HIDDEN IMPORTS: This forces PyInstaller to bundle libraries from your requirements.txt
    hiddenimports=[
        'sklearn',
        'torch',
        'torchvision',
        'flask',
        'authlib',
        'psycopg2',
        'pymongo',
        'docx',
        'PyPDF2',
        'openpyxl',
        'pptx',
        'pandas',
        'numpy',
        'joblib',
        'deep_translator'
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
    [],
    exclude_binaries=True,
    name='Kemaslah',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=True,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)
coll = COLLECT(
    exe,
    a.binaries,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name='Kemaslah',
)
