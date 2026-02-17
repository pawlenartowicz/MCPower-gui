"""Entry point for `python -m mcpower_gui`."""

import os
import shutil
import sys
from pathlib import Path

from PySide6.QtGui import QIcon
from PySide6.QtWidgets import QApplication

from mcpower_gui import __version__


def _install_linux_desktop_integration() -> None:
    """Install .desktop file and icon so Linux DEs show the app icon."""
    if sys.platform != "linux":
        return

    pkg_dir = Path(__file__).parent
    data_home = Path(os.environ.get("XDG_DATA_HOME", Path.home() / ".local" / "share"))

    # Install icon to XDG icon directory
    icon_src = pkg_dir / "media" / "icon.png"
    icon_dst = (
        data_home
        / "icons"
        / "hicolor"
        / "256x256"
        / "apps"
        / "pl.freestylerscientist.mcpower.png"
    )
    if icon_src.exists() and (
        not icon_dst.exists() or icon_src.stat().st_mtime > icon_dst.stat().st_mtime
    ):
        icon_dst.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(icon_src, icon_dst)

    # Install .desktop file
    desktop_src = pkg_dir / "pl.freestylerscientist.mcpower.desktop"
    desktop_dst = data_home / "applications" / "pl.freestylerscientist.mcpower.desktop"
    if desktop_src.exists() and (
        not desktop_dst.exists()
        or desktop_src.stat().st_mtime > desktop_dst.stat().st_mtime
    ):
        desktop_dst.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(desktop_src, desktop_dst)


def _smoke_test() -> None:
    """Run a comprehensive self-check without opening a window, then exit."""
    # Use offscreen platform — smoke test needs no real display
    os.environ["QT_QPA_PLATFORM"] = "offscreen"

    errors: list[str] = []

    # 1. Critical imports
    try:
        import mcpower  # noqa: F401
    except ImportError as e:
        errors.append(f"mcpower import failed: {e}")
    try:
        import PySide6  # noqa: F401
    except ImportError as e:
        errors.append(f"PySide6 import failed: {e}")
    try:
        import pyqtgraph  # noqa: F401
    except ImportError as e:
        errors.append(f"pyqtgraph import failed: {e}")

    # 2. Qt initialization
    app = QApplication.instance() or QApplication(sys.argv)
    if app is None:
        errors.append("QApplication creation failed")

    from mcpower_gui.theme import apply_font_size, apply_theme

    apply_theme()
    apply_font_size()

    # 3. MainWindow creation
    try:
        from mcpower_gui.app import MainWindow

        window = MainWindow()
        del window
    except Exception as e:
        errors.append(f"MainWindow creation failed: {e}")

    # 4. Bundled resources
    from mcpower_gui._resources import resource_path

    for name in ["media/cat.gif", "media/icon.png", "acknowledgments.txt"]:
        p = resource_path(name)
        if not p.exists():
            errors.append(f"Missing resource: {name}")

    docs_dir = resource_path("docs")
    if docs_dir.is_dir():
        md_files = list(docs_dir.glob("*.md"))
        if not md_files:
            errors.append("No docs/*.md files found")
    else:
        errors.append("docs/ directory not found")

    # 5. Core logic modules
    try:
        from mcpower_gui.state import ModelState

        state = ModelState()
        state.snapshot()
    except Exception as e:
        errors.append(f"ModelState failed: {e}")
    try:
        from mcpower_gui.script_generator import generate_script  # noqa: F401
    except ImportError as e:
        errors.append(f"script_generator import failed: {e}")
    try:
        from mcpower_gui.history_manager import HistoryManager  # noqa: F401
    except ImportError as e:
        errors.append(f"HistoryManager import failed: {e}")

    # 6. Report result
    if errors:
        print("SMOKE TEST FAILED:", file=sys.stderr)
        for err in errors:
            print(f"  - {err}", file=sys.stderr)
        sys.exit(1)

    print(f"mcpower-gui {__version__}")
    sys.exit(0)


def main():
    if "--smoke-test" in sys.argv:
        _smoke_test()

    _install_linux_desktop_integration()

    app = QApplication(sys.argv)
    app.setApplicationName("MCPower")
    app.setApplicationVersion(__version__)
    app.setDesktopFileName("pl.freestylerscientist.mcpower")

    from mcpower_gui.theme import apply_font_size, apply_theme

    apply_theme()
    apply_font_size()

    icon_path = Path(__file__).parent / "media" / "icon.png"
    if icon_path.exists():
        app.setWindowIcon(QIcon(str(icon_path)))

    from mcpower_gui.app import MainWindow

    window = MainWindow()
    window.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
