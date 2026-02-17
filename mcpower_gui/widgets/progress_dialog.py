"""Pop-up dialog with animated cat and progress bar shown during analysis."""

from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QMovie
from PySide6.QtWidgets import QDialog, QLabel, QProgressBar, QPushButton, QVBoxLayout

from mcpower_gui._resources import resource_path
from mcpower_gui.theme import ThemeMode, current_mode


class ProgressDialog(QDialog):
    """Modal-style progress dialog with a cat animation and progress bar."""

    abandon_requested = Signal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Running Analysis...")
        self.setFixedSize(580, 500)
        self.setWindowFlags(
            self.windowFlags() & ~Qt.WindowContextHelpButtonHint | Qt.WindowTitleHint
        )

        self._cancelling = False

        layout = QVBoxLayout(self)
        layout.setAlignment(Qt.AlignCenter)

        # Cat animation
        self._gif_label = QLabel()
        self._gif_label.setAlignment(Qt.AlignCenter)
        gif_path = str(resource_path("media", "cat.gif"))
        self._movie = QMovie(gif_path)
        self._gif_label.setMovie(self._movie)
        layout.addWidget(self._gif_label)

        # Progress bar
        self._progress_bar = QProgressBar()
        self._progress_bar.setFixedWidth(400)
        self._progress_bar.setFormat("%p% (%v / %m simulations)")
        layout.addWidget(self._progress_bar, alignment=Qt.AlignCenter)

        # Abandon button
        self._abandon_btn = QPushButton("Abandon Simulation")
        self._abandon_btn.setFixedWidth(200)
        self._abandon_btn.clicked.connect(self._on_abandon_clicked)
        layout.addWidget(self._abandon_btn, alignment=Qt.AlignCenter)

    def _on_abandon_clicked(self):
        self.set_cancelling()
        self.abandon_requested.emit()

    def set_cancelling(self):
        """Switch to cancelling visual state."""
        self._cancelling = True
        self._abandon_btn.setEnabled(False)
        self._abandon_btn.setText("Cancelling...")

    def start(self):
        """Reset progress and show the dialog with animation."""
        self._cancelling = False
        self._abandon_btn.setEnabled(True)
        self._abandon_btn.setText("Abandon Simulation")
        self._progress_bar.setValue(0)
        # Pick gif based on current theme
        gif_name = "cat_dp.gif" if current_mode() == ThemeMode.DARK_PINK else "cat.gif"
        gif_path = str(resource_path("media", gif_name))
        self._movie = QMovie(gif_path)
        self._gif_label.setMovie(self._movie)
        self._movie.start()
        self.show()

    def update_progress(self, current: int, total: int):
        """Update the progress bar values."""
        self._progress_bar.setMaximum(total)
        self._progress_bar.setValue(current)

    def stop(self):
        """Stop the animation and close the dialog."""
        self._movie.stop()
        self.close()

    def closeEvent(self, event):
        """Prevent closing the dialog by the user (X button) while running."""
        if self._cancelling:
            # Allow close when cancellation is in progress
            self._movie.stop()
            super().closeEvent(event)
        elif self._movie.state() == QMovie.Running:
            event.ignore()
        else:
            super().closeEvent(event)
