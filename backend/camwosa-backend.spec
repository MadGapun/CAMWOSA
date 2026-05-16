# PyInstaller-Spec fuer CAMWOSA-Backend.
#
# Bundle Erzeugen:
#   pip install pyinstaller
#   pyinstaller camwosa-backend.spec
#
# Ergebnis: dist/camwosa-backend(.exe)
#
# Wird vom Electron-App-Bundle als Subprozess gestartet.

# -*- mode: python ; coding: utf-8 -*-

block_cipher = None

a = Analysis(
    ['camwosa/api/app.py'],
    pathex=[],
    binaries=[],
    datas=[
        # Default-Profile mitbundeln (relativ zum Backend)
        ('../data', 'data'),
    ],
    hiddenimports=[
        'camwosa.postprocessor.grbl_standard',
        'camwosa.postprocessor.grbl_genmitsu',
        'camwosa.postprocessor.grbl_genmitsu_rotary_y',
        'camwosa.cad.dxf_importer',
        'camwosa.cad.svg_importer',
        'camwosa.cad.stl_importer',
        'camwosa.cad.step_importer',
        'shapely.geometry',
        'pyclipper',
        'ezdxf',
        'trimesh',
        'rtree',
        'reportlab',
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=['matplotlib', 'IPython', 'tkinter'],
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
    name='camwosa-backend',
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
)
