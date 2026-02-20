# -*- mode: python ; coding: utf-8 -*-
"""PyInstaller spec for MCPower GUI.

Build on each target OS:
    # Linux   → produces dist/MCPower  (ELF binary)
    # Windows → produces dist/MCPower.exe
    # macOS   → produces dist/MCPower.app  (app bundle — double-click to open)
    pyinstaller mcpower-gui.spec
"""

import re
import sys
from pathlib import Path

from PyInstaller.utils.hooks import copy_metadata

block_cipher = None

# ── Version (read from pyproject.toml — single source of truth) ──
_pyproject = Path("pyproject.toml").read_text(encoding="utf-8")
_version_match = re.search(r'^version\s*=\s*"([^"]+)"', _pyproject, re.MULTILINE)
_version = _version_match.group(1) if _version_match else "0.0.0"

# ── Paths ────────────────────────────────────────────────────────
pkg_dir = Path("mcpower_gui")

# ── Data files bundled into the frozen app ───────────────────────
# copy_metadata bundles the .dist-info directory so that
# importlib.metadata.version("MCPower") works in the frozen app.
datas = [
    (str(pkg_dir / "media"), "mcpower_gui/media"),
    (str(pkg_dir / "pl.freestylerscientist.mcpower.desktop"), "mcpower_gui"),
    (str(pkg_dir / "acknowledgments.txt"), "mcpower_gui"),
    (str(pkg_dir / "docs"), "mcpower_gui/docs"),
    (str(pkg_dir / "tips.yaml"), "mcpower_gui"),
] + copy_metadata("MCPower") + copy_metadata("mcpower-gui")

# ── Icon (per-OS format) ─────────────────────────────────────────
if sys.platform == "win32":
    app_icon = str(pkg_dir / "media" / "icon.ico")
elif sys.platform == "darwin":
    app_icon = str(pkg_dir / "media" / "icon.icns")
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
    excludes=[
        "tkinter",
        # matplotlib chain — installed as MCPower dep but not used by GUI
        "matplotlib", "mpl_toolkits", "PIL", "Pillow",
        "kiwisolver", "contourpy", "cycler", "fonttools", "pyparsing",
        # IPython/Jupyter chain — pulled via pyqtgraph optional console
        "IPython", "jedi", "parso", "pygments",
        "prompt_toolkit", "traitlets", "tornado", "zmq",
        "ipykernel", "jupyter_client", "jupyter_core", "debugpy", "pexpect",
        # statsmodels — optional MCPower[lme] dep, not needed in GUI
        "statsmodels",
        # Test/build tools
        "_pytest", "pytest", "pluggy", "coverage",
        "setuptools", "pkg_resources",
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
    name="MCPower",
    icon=app_icon,
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=False,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,  # windowed app, no terminal
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)

# macOS: wrap the EXE in a proper .app bundle so Finder treats it as a GUI app.
# Without this, macOS opens the bare binary in Terminal instead.
if sys.platform == "darwin":
    app = BUNDLE(
        exe,
        name="MCPower.app",
        icon=app_icon,
        bundle_identifier="pl.freestylerscientist.mcpower",
        info_plist={
            "CFBundleName": "MCPower",
            "CFBundleDisplayName": "MCPower",
            "CFBundleVersion": _version,
            "CFBundleShortVersionString": _version,
            "NSHighResolutionCapable": True,
            "NSPrincipalClass": "NSApplication",
            "NSAppleScriptEnabled": False,
        },
    )
