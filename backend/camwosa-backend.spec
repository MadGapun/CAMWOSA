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
        # Postprozessoren (Plugin-Discovery)
        'camwosa.postprocessor.grbl_standard',
        'camwosa.postprocessor.grbl_genmitsu',
        'camwosa.postprocessor.grbl_genmitsu_rotary_y',
        # CAD-Importer (Plugin-Discovery)
        'camwosa.cad.dxf_importer',
        'camwosa.cad.svg_importer',
        'camwosa.cad.stl_importer',
        'camwosa.cad.step_importer',
        'camwosa.cad.text_zu_pfad',
        # CAM-Module
        'camwosa.cam.kontur',
        'camwosa.cam.tasche',
        'camwosa.cam.bohren',
        'camwosa.cam.gravur',
        'camwosa.cam.relief',
        'camwosa.cam.spezial',
        'camwosa.cam.pcb',
        'camwosa.cam.bohrbild',
        'camwosa.cam.drechseln',
        'camwosa.cam.wrap',
        'camwosa.cam.rotary',
        'camwosa.cam.simulation',
        # G-Code-Post-Processing + Feeds + Zeit (teils lazy in Endpoints importiert)
        'camwosa.gcode.fahrweg',
        'camwosa.gcode.arc_fitting',
        'camwosa.gcode.zeit_schaetzung',
        'camwosa.feeds.rechner',
        'camwosa.db.werkzeug_name',
        # STL/Heightmap Pipeline (Bild-zu-Relief A33/A35/A36)
        'camwosa.stl.heightmap',
        'camwosa.stl.bild_heightmap',
        'camwosa.stl.heightmap_bearbeitung',
        'camwosa.stl.ai_tiefenkarte',
        # API-Endpoints (Blueprint-Discovery — werden zur Laufzeit importiert)
        'camwosa.api.endpoints.heightmap',
        'camwosa.api.endpoints.text',
        'camwosa.api.endpoints.wrap',
        'camwosa.api.endpoints.simulation',
        'camwosa.api.endpoints.quickcam',
        'camwosa.api.endpoints.annotationen',
        'camwosa.api.endpoints.cutting_presets',
        'camwosa.api.openapi',
        # Workflow + QuickCAM
        'camwosa.workflow.auto_cam',
        'camwosa.workflow.gcode_schritte',
        'camwosa.workflow.annotationen_zu_operationen',
        'camwosa.quickcam.templates',
        # Third-Party — alle die PyInstaller manchmal nicht erkennt
        'shapely.geometry',
        'pyclipper',
        'ezdxf',
        'trimesh',
        'rtree',
        'reportlab',
        'numpy',
        'pydantic',
        'PIL.Image',
        'fontTools.ttLib',
        'fontTools.pens.basePen',
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[
        'matplotlib', 'IPython', 'tkinter',
        # AI-Extra ist optional und HUGE — niemals in Default-Bundle
        'torch', 'transformers', 'tensorflow', 'safetensors',
        # Test-Infrastruktur
        'pytest', 'hypothesis', 'pytest_cov',
        # Dev-Tools
        'ruff', 'black', 'mypy',
        # Jupyter etc.
        'notebook', 'jupyter',
    ],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

# One-folder mode: kompakter und schneller im Start als One-file.
# electron-builder kopiert das ganze Folder via extraResources.
exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name='camwosa-backend',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=False,  # UPX kann Defender-False-Positives ausloesen
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
    a.zipfiles,
    a.datas,
    strip=False,
    upx=False,
    upx_exclude=[],
    name='camwosa-backend',
)
