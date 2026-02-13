"""Entry point for `python -m mcpower_gui`."""

import sys
from pathlib import Path

from PySide6.QtGui import QIcon
from PySide6.QtWidgets import QApplication

from mcpower_gui import __version__


def _smoke_test() -> None:
    """Run a comprehensive self-check without opening a window, then exit."""
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

    # 3. MainWindow creation
    try:
        from mcpower_gui.app import MainWindow

        window = MainWindow()
        del window
    except Exception as e:
        errors.append(f"MainWindow creation failed: {e}")

    # 4. Bundled resources
    from mcpower_gui._resources import resource_path

    for name in ["cat.gif", "icon.png", "acknowledgments.txt"]:
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

    app = QApplication(sys.argv)
    app.setApplicationName("MCPower")
    app.setApplicationVersion(__version__)
    app.setDesktopFileName("pl.freestylerscientist.mcpower")

    icon_path = Path(__file__).parent / "icon.png"
    if icon_path.exists():
        app.setWindowIcon(QIcon(str(icon_path)))

    from mcpower_gui.app import MainWindow

    window = MainWindow()
    window.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
