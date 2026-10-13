"""
Reusable widgets and small UI helpers for SmolLM Studio.
"""

from PyQt6.QtCore import QRectF, Qt, pyqtSignal
from PyQt6.QtGui import QColor, QFocusEvent, QFont, QIcon, QKeyEvent, QLinearGradient, QPainter, QPixmap
from PyQt6.QtWidgets import QFrame, QHBoxLayout, QLabel, QPlainTextEdit, QWidget

from styles import UI_FONT_FAMILY, Palette


def create_app_icon(size: int = 64) -> QIcon:
    """Draw the app icon at runtime so no binary asset needs bundling."""
    pixmap = QPixmap(size, size)
    pixmap.fill(Qt.GlobalColor.transparent)

    painter = QPainter(pixmap)
    painter.setRenderHint(QPainter.RenderHint.Antialiasing)
    gradient = QLinearGradient(0, 0, size, size)
    gradient.setColorAt(0.0, QColor(Palette.ACCENT_HOVER))
    gradient.setColorAt(1.0, QColor(Palette.ASSISTANT))
    painter.setBrush(gradient)
    painter.setPen(Qt.PenStyle.NoPen)
    radius = size * 0.22
    painter.drawRoundedRect(QRectF(0, 0, size, size), radius, radius)

    font = QFont(UI_FONT_FAMILY)
    font.setBold(True)
    font.setPixelSize(int(size * 0.55))
    painter.setFont(font)
    painter.setPen(QColor("#ffffff"))
    painter.drawText(pixmap.rect(), Qt.AlignmentFlag.AlignCenter, "S")
    painter.end()
    return QIcon(pixmap)


def make_section_header(text: str) -> QLabel:
    label = QLabel(text)
    label.setObjectName("sectionHeader")
    return label


def make_field_label(text: str, tooltip: str = "") -> QLabel:
    label = QLabel(text)
    label.setObjectName("fieldLabel")
    if tooltip:
        label.setToolTip(tooltip)
    return label


def make_divider() -> QFrame:
    divider = QFrame()
    divider.setObjectName("divider")
    return divider


class StatusIndicator(QWidget):
    """Colored dot + caption, e.g. '● 就緒'."""

    COLORS: dict[str, str] = {
        "idle": Palette.TEXT_SUBTLE,
        "ready": Palette.SUCCESS,
        "busy": Palette.WARNING,
        "error": Palette.DANGER,
        "remote": Palette.ACCENT_TEXT,
    }

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(7)

        self._dot = QLabel()
        self._dot.setFixedSize(8, 8)
        self._text = QLabel()
        self._text.setObjectName("caption")
        self._text.setWordWrap(True)

        layout.addWidget(self._dot, 0, Qt.AlignmentFlag.AlignVCenter)
        layout.addWidget(self._text, 1)
        self._state = ""
        self.set_state("idle", "")

    @property
    def state(self) -> str:
        return self._state

    def set_state(self, state: str, text: str) -> None:
        color = self.COLORS.get(state, Palette.TEXT_SUBTLE)
        self._dot.setStyleSheet(f"background-color: {color}; border-radius: 4px;")
        self._text.setText(text)
        self._state = state


class ChatInputEdit(QPlainTextEdit):
    """Auto-growing composer: Enter submits, Shift+Enter inserts a newline."""

    submitted = pyqtSignal()
    focus_changed = pyqtSignal(bool)

    MIN_HEIGHT = 40
    MAX_HEIGHT = 168

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setObjectName("composerInput")
        self.setTabChangesFocus(True)
        self.document().contentsChanged.connect(self._adjust_height)
        self._adjust_height()

    def keyPressEvent(self, event: QKeyEvent) -> None:
        is_enter = event.key() in (Qt.Key.Key_Return, Qt.Key.Key_Enter)
        if is_enter and not event.modifiers() & Qt.KeyboardModifier.ShiftModifier:
            self.submitted.emit()
            return
        super().keyPressEvent(event)

    def focusInEvent(self, event: QFocusEvent) -> None:
        super().focusInEvent(event)
        self.focus_changed.emit(True)

    def focusOutEvent(self, event: QFocusEvent) -> None:
        super().focusOutEvent(event)
        self.focus_changed.emit(False)

    def _adjust_height(self) -> None:
        # QPlainTextDocumentLayout reports document height in lines.
        line_count = max(1, int(self.document().size().height()))
        content = line_count * self.fontMetrics().lineSpacing()
        chrome = int(self.document().documentMargin() * 2) + self.contentsMargins().top() + self.contentsMargins().bottom()
        self.setFixedHeight(max(self.MIN_HEIGHT, min(self.MAX_HEIGHT, content + chrome + 6)))
