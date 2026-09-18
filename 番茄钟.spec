# -*- mode: python ; coding: utf-8 -*-

import sys

sys.path.insert(0, SPECPATH)
from pomodoro import __version__  # noqa: E402

APP_NAME = f"TomatoClock-v{__version__}"

a = Analysis(
    ['main.py'],
    pathex=[],
    binaries=[],
    datas=[('assets/tomato.png', 'assets')],
    hiddenimports=['pystray', 'PIL', 'PIL.Image', 'PIL.ImageDraw', 'PIL.ImageTk'],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    # 去掉 Pillow/pystray 依赖链误带的构建工具，减小体积
    excludes=[
        'setuptools', 'pkg_resources', 'pip', 'wheel',
        'distutils', 'lib2to3', 'unittest', 'pydoc', 'doctest',
    ],
    noarchive=False,
    optimize=0,
)
pyz = PYZ(a.pure)

# onedir：EXE 不再自带 binaries/datas，交给 COLLECT，启动时无需解压到临时目录
exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name=APP_NAME,
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=False,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon=['assets/tomato.ico'],
    version='version_info.txt',
)

coll = COLLECT(
    exe,
    a.binaries,
    a.datas,
    strip=False,
    upx=False,
    upx_exclude=[],
    name=APP_NAME,
)
