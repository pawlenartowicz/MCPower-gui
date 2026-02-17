"""Documentation dialog — sidebar navigation + markdown viewer."""

from __future__ import annotations

from PySide6.QtWidgets import (
    QDialog,
    QDialogButtonBox,
    QHBoxLayout,
    QListWidget,
    QTextBrowser,
    QVBoxLayout,
    QWidget,
)

from mcpower_gui._resources import resource_path

_PAGES: list[tuple[str, str]] = [
    ("Overview", "overview.md"),
    ("Model Tab", "model_tab.md"),
    ("Analysis Tab", "analysis_tab.md"),
    ("Results Tab", "results_tab.md"),
    ("Settings", "settings.md"),
    ("Key Concepts", "key_concepts.md"),
]


def _load_doc_page(filename: str) -> str:
    return resource_path("docs", filename).read_text(encoding="utf-8")


class DocumentationDialog(QDialog):
    def __init__(self, parent: QWidget | None = None, initial_page: str | None = None):
        super().__init__(parent)
        self.setWindowTitle("Documentation")
        self.resize(780, 560)

        root = QVBoxLayout(self)

        body = QHBoxLayout()

        self._sidebar = QListWidget()
        self._sidebar.setFixedWidth(170)
        for display_name, _ in _PAGES:
            self._sidebar.addItem(display_name)
        body.addWidget(self._sidebar)

        self._browser = QTextBrowser()
        self._browser.setOpenExternalLinks(True)
        body.addWidget(self._browser, stretch=1)

        root.addLayout(body, stretch=1)

        buttons = QDialogButtonBox(QDialogButtonBox.StandardButton.Close)
        buttons.rejected.connect(self.close)
        root.addWidget(buttons)

        self._sidebar.currentRowChanged.connect(self._on_page_changed)
        start_row = 0
        if initial_page:
            for i, (name, _) in enumerate(_PAGES):
                if name == initial_page:
                    start_row = i
                    break
        self._sidebar.setCurrentRow(start_row)

    def _on_page_changed(self, row: int):
        if 0 <= row < len(_PAGES):
            _, filename = _PAGES[row]
            text = _load_doc_page(filename)
            self._browser.setMarkdown(text)
