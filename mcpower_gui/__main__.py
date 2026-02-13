"""Entry point for `python -m mcpower_gui`."""

import sys
from pathlib import Path

from PySide6.QtGui import QIcon
from PySide6.QtWidgets import QApplication

from mcpower_gui import __version__
from mcpower_gui.app import MainWindow


def main():
    app = QApplication(sys.argv)
    app.setApplicationName("MCPower")
    app.setApplicationVersion(__version__)
    app.setDesktopFileName("pl.freestylerscientist.mcpower")

    icon_path = Path(__file__).parent / "icon.png"
    if icon_path.exists():
        app.setWindowIcon(QIcon(str(icon_path)))

    window = MainWindow()
    window.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
