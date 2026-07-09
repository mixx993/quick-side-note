# -*- mode: python ; coding: utf-8 -*-


a = Analysis(
    ["quick_note.py"],
    pathex=[],
    binaries=[],
    datas=[("assets", "assets")],
    hiddenimports=[
        "winsdk.windows.globalization",
        "winsdk.windows.graphics.imaging",
        "winsdk.windows.media.ocr",
        "winsdk.windows.storage",
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
    name="QuickSideNote",
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
    version="QuickSideNote_version_info.txt",
    entitlements_file=None,
    icon=["assets\\quick_note_icon.ico"],
)
