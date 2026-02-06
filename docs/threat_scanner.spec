# -*- mode: python ; coding: utf-8 -*-
"""
PyInstaller spec file for Quantum-Enhanced Threat Scanner
Build with: pyinstaller threat_scanner.spec
"""

block_cipher = None

a = Analysis(
    ['scanner/threat_scanner.py'],
    pathex=[],
    binaries=[],
    datas=[
        ('models/*.pkl', 'models'),
        ('phase4/models/*.dill', 'phase4/models'),
        ('phase4/models/*.pkl', 'phase4/models'),
        ('phase4/models/*.json', 'phase4/models'),
    ],
    hiddenimports=[
        'sklearn.ensemble',
        'sklearn.tree',
        'sklearn.utils._weight_vector',
        'pefile',
        'lief',
        'dill',
        'tldextract',
        'qiskit',
        'pennylane',
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[
        'matplotlib',
        'notebook',
        'jupyter',
        'IPython',
    ],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.zipfiles,
    a.datas,
    [],
    name='ThreatScanner',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=True,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon=None,  # Add icon path here if you have one
)
