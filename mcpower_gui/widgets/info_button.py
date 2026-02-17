"""Info button with documentation popup for QGroupBox headers."""

from __future__ import annotations

from PySide6.QtCore import QEvent, QObject, QPoint, Qt
from PySide6.QtGui import QFontMetrics
from PySide6.QtWidgets import (
    QFrame,
    QGroupBox,
    QHBoxLayout,
    QPushButton,
    QTextBrowser,
    QVBoxLayout,
    QWidget,
)

from mcpower_gui._resources import resource_path


def extract_doc_section(doc_file: str, section_heading: str) -> str:
    """Extract a ``## section_heading`` block from a docs markdown file.

    Returns everything from the heading line to the next ``## `` heading
    (or EOF), inclusive of the heading itself.
    """
    path = resource_path("docs", doc_file)
    text = path.read_text(encoding="utf-8")
    lines = text.split("\n")

    target = f"## {section_heading}"
    start_idx: int | None = None
    for i, line in enumerate(lines):
        if line.strip() == target:
            start_idx = i
            break

    if start_idx is None:
        return f"*Documentation section '{section_heading}' not found.*"

    end_idx = len(lines)
    for i in range(start_idx + 1, len(lines)):
        if lines[i].startswith("## "):
            end_idx = i
            break

    return "\n".join(lines[start_idx:end_idx]).strip()


class InfoPopup(QFrame):
    """Frameless popup showing a rendered markdown section."""

    _POPUP_WIDTH = 480

    def __init__(
        self,
        markdown_text: str,
        doc_page_name: str,
        parent: QWidget | None = None,
    ):
        super().__init__(parent, Qt.WindowType.Popup)
        self._doc_page_name = doc_page_name

        layout = QVBoxLayout(self)
        layout.setContentsMargins(8, 8, 8, 8)

        self._browser = QTextBrowser()
        self._browser.setOpenExternalLinks(True)
        self._browser.setFrameShape(QFrame.Shape.NoFrame)
        self._browser.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self._browser.setHorizontalScrollBarPolicy(
            Qt.ScrollBarPolicy.ScrollBarAlwaysOff
        )
        self._browser.setMarkdown(markdown_text)
        self._browser.document().setTextWidth(self._POPUP_WIDTH - 24)

        doc_height = int(self._browser.document().size().height()) + 4
        self._browser.setFixedHeight(doc_height)
        self._browser.setFixedWidth(self._POPUP_WIDTH - 16)
        layout.addWidget(self._browser)

        link = QPushButton("Open full documentation...")
        link.setFlat(True)
        link.setCursor(Qt.CursorShape.PointingHandCursor)
        link.setStyleSheet(
            "QPushButton { color: palette(link); text-align: left; padding: 2px; }"
            "QPushButton:hover { text-decoration: underline; }"
        )
        link.clicked.connect(self._open_docs)
        row = QHBoxLayout()
        row.addWidget(link)
        row.addStretch()
        layout.addLayout(row)

        self.setFixedWidth(self._POPUP_WIDTH)
        self.setStyleSheet(
            "InfoPopup { background: palette(base); border: 1px solid palette(mid); }"
        )

    def _open_docs(self):
        self.close()
        from mcpower_gui.widgets.documentation_dialog import DocumentationDialog

        top = self.parent()
        while top is not None and top.parent() is not None:
            top = top.parent()
        dlg = DocumentationDialog(top, initial_page=self._doc_page_name)
        dlg.exec()


class InfoButton(QPushButton):
    """Small circular (i) button that shows a documentation popup on click."""

    def __init__(
        self,
        doc_file: str,
        section_heading: str,
        doc_page_name: str,
        parent: QWidget | None = None,
    ):
        super().__init__("i", parent)
        self._doc_file = doc_file
        self._section_heading = section_heading
        self._doc_page_name = doc_page_name

        self.setFixedSize(16, 16)
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.setToolTip("Show help")
        self.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        self.setStyleSheet(
            "QPushButton {"
            "  border: 1px solid palette(mid);"
            "  border-radius: 8px;"
            "  font-size: 10px;"
            "  font-weight: bold;"
            "  font-style: italic;"
            "  padding: 0px;"
            "  background: transparent;"
            "  color: palette(text);"
            "}"
            "QPushButton:hover {"
            "  background: palette(highlight);"
            "  color: palette(highlighted-text);"
            "}"
        )
        self.clicked.connect(self._show_popup)

    def _show_popup(self):
        text = extract_doc_section(self._doc_file, self._section_heading)
        popup = InfoPopup(text, self._doc_page_name, parent=self)
        pos = self.mapToGlobal(QPoint(0, self.height() + 4))

        screen = self.screen()
        if screen:
            geo = screen.availableGeometry()
            popup.adjustSize()
            if pos.y() + popup.height() > geo.bottom():
                pos = self.mapToGlobal(QPoint(0, -popup.height() - 4))
            if pos.x() + popup.width() > geo.right():
                pos.setX(geo.right() - popup.width())

        popup.move(pos)
        popup.show()


class _InfoPositioner(QObject):
    """Event filter that keeps an InfoButton next to a QGroupBox title."""

    def __init__(self, group_box: QGroupBox, btn: InfoButton):
        super().__init__(group_box)
        self._group = group_box
        self._btn = btn
        btn.setParent(group_box)
        btn.raise_()
        group_box.installEventFilter(self)
        self._reposition()

    def eventFilter(self, obj: QObject, event: QEvent) -> bool:
        if obj is self._group and event.type() in (
            QEvent.Type.Resize,
            QEvent.Type.Show,
            QEvent.Type.LayoutRequest,
        ):
            self._reposition()
        return False

    def _reposition(self):
        fm = QFontMetrics(self._group.font())
        title_w = fm.horizontalAdvance(self._group.title())
        x = title_w + 14
        title_h = fm.height()
        y = max(0, (title_h - self._btn.height()) // 2)
        self._btn.move(x, y)


def attach_info_button(
    group_box: QGroupBox,
    doc_file: str,
    section_heading: str,
    doc_page_name: str,
) -> InfoButton:
    """Attach an (i) info button next to a QGroupBox title.

    The button is positioned automatically via an event filter.
    Returns the created InfoButton.
    """
    btn = InfoButton(doc_file, section_heading, doc_page_name)
    _InfoPositioner(group_box, btn)
    return btn
