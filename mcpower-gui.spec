# -*- mode: python ; coding: utf-8 -*-
"""PyInstaller spec for MCPower GUI.

Build on each target OS:
    # Linux  → produces dist/MCPower  (ELF binary)
    # Windows → produces dist/MCPower.exe
    pyinstaller mcpower-gui.spec
"""

import sys
from pathlib import Path

block_cipher = None

# ── Paths ────────────────────────────────────────────────────────
pkg_dir = Path("mcpower_gui")

# ── Data files bundled into the frozen app ───────────────────────
datas = [
    (str(pkg_dir / "cat.gif"), "mcpower_gui"),
    (str(pkg_dir / "icon.png"), "mcpower_gui"),
    (str(pkg_dir / "acknowledgments.txt"), "mcpower_gui"),
    (str(pkg_dir / "docs"), "mcpower_gui/docs"),
]

# ── Icon (per-OS format) ─────────────────────────────────────────
if sys.platform == "win32":
    app_icon = str(pkg_dir / "icon.ico")
elif sys.platform == "darwin":
    app_icon = str(pkg_dir / "icon.icns")
else:
    app_icon = None

# ── Hidden imports that PyInstaller cannot detect automatically ──
# MCPower uses conditional / lazy imports for optional backends.
hiddenimports = [
    # MCPower core
    "mcpower",
    "mcpower.model",
    "mcpower.utils.parsers",
    # Stats (imported inside functions)
    "scipy.stats",
    "statsmodels.regression.mixed_linear_model",
    # Optional parallel backend
    "joblib",
    # multiprocessing freeze support
    "multiprocessing",
]

# Optional: Numba JIT — only include if installed
try:
    import numba  # noqa: F401
    hiddenimports.append("numba")
except ImportError:
    pass

# Optional: compiled C++ backend
try:
    import mcpower_native  # noqa: F401
    hiddenimports.append("mcpower_native")
except ImportError:
    pass

# ── Analysis ─────────────────────────────────────────────────────
a = Analysis(
    [str(pkg_dir / "__main__.py")],
    pathex=["."],
    binaries=[],
    datas=datas,
    hiddenimports=hiddenimports,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=["tkinter", "test", "unittest"],
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
    name="MCPower",
    icon=app_icon,
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,  # windowed app, no terminal
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)
