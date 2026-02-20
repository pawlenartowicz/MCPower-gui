"""Info button with documentation popup for QGroupBox headers."""

from __future__ import annotations

from PySide6.QtCore import QEvent, QObject, QPoint, Qt
from PySide6.QtGui import QFont, QFontMetrics
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


def _load_doc_file(doc_file: str) -> str:
    """Load the full contents of a docs markdown file."""
    path = resource_path("docs", doc_file)
    return path.read_text(encoding="utf-8")


class InfoPopup(QFrame):
    """Frameless popup showing a rendered markdown page."""

    _POPUP_WIDTH = 480

    def __init__(
        self,
        markdown_text: str,
        doc_file: str,
        parent: QWidget | None = None,
    ):
        super().__init__(parent, Qt.WindowType.Popup)
        self._doc_file = doc_file

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
        dlg = DocumentationDialog(top, initial_page=self._doc_file)
        dlg.exec()


class InfoButton(QPushButton):
    """Small circular (?) button that shows a documentation popup on click."""

    def __init__(
        self,
        doc_file: str,
        parent: QWidget | None = None,
    ):
        super().__init__("?", parent)
        self._doc_file = doc_file

        self.setFixedSize(20, 20)
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.setToolTip("Show help")
        self.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        self.setStyleSheet(
            "QPushButton {"
            "  border: 1px solid palette(mid);"
            "  border-radius: 10px;"
            "  font-size: 12px;"
            "  font-weight: bold;"
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
        text = _load_doc_file(self._doc_file)
        popup = InfoPopup(text, self._doc_file, parent=self)
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


class TitleWidgetPositioner(QObject):
    """Event filter that positions a child widget next to a QGroupBox title.

    ``x_offset`` is the horizontal gap from the left edge of the group box
    to where the widget is placed (added after the title text width).
    """

    def __init__(
        self,
        group_box: QGroupBox,
        widget: QWidget,
        x_offset: int = 22,
        title_bold: bool = False,
    ):
        super().__init__(group_box)
        self._group = group_box
        self._widget = widget
        self._x_offset = x_offset
        self._title_bold = title_bold
        widget.setParent(group_box)
        widget.raise_()
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
        font = QFont(self._group.font())
        if self._title_bold:
            font.setBold(True)
        fm = QFontMetrics(font)
        title_w = fm.horizontalAdvance(self._group.title())
        x = title_w + self._x_offset
        title_h = fm.height()
        y = max(0, (title_h - self._widget.height()) // 2)
        self._widget.move(x, y)


def attach_info_button(
    group_box: QGroupBox,
    doc_file: str,
    title_bold: bool = False,
) -> InfoButton:
    """Attach a (?) info button next to a QGroupBox title.

    The button is positioned automatically via an event filter.
    Returns the created InfoButton.
    """
    btn = InfoButton(doc_file)
    TitleWidgetPositioner(group_box, btn, x_offset=22, title_bold=title_bold)
    return btn
