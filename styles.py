"""
Design tokens and Qt style sheets for SmolLM Studio.

The palette is a neutral, low-contrast dark theme (GitHub Dark-inspired) so
that content, not chrome, draws the eye. Reference `Palette` tokens instead of
hard-coding hex values anywhere else in the UI.
"""

from typing import Final


class Palette:
    """Central color tokens."""

    BG: Final = "#0d1117"
    SURFACE: Final = "#161b22"
    ELEVATED: Final = "#21262d"
    BORDER: Final = "#30363d"
    BORDER_MUTED: Final = "#21262d"
    BORDER_STRONG: Final = "#484f58"
    TEXT: Final = "#e6edf3"
    TEXT_MUTED: Final = "#8b949e"
    TEXT_SUBTLE: Final = "#6e7681"
    ACCENT: Final = "#1f6feb"
    ACCENT_HOVER: Final = "#388bfd"
    ACCENT_TEXT: Final = "#58a6ff"
    ASSISTANT: Final = "#8957e5"
    SUCCESS: Final = "#3fb950"
    WARNING: Final = "#d29922"
    DANGER: Final = "#f85149"
    DANGER_STRONG: Final = "#da3633"
    CODE_BG: Final = "#010409"
    INLINE_CODE: Final = "#ffa657"


UI_FONT_FAMILY: Final = "Segoe UI"
MONO_FONT_STACK: Final = "'Cascadia Mono', 'Consolas', 'Courier New', monospace"
CHAT_FONT_STACK: Final = "'Segoe UI', 'Microsoft JhengHei UI', 'PingFang TC', sans-serif"

_P = Palette

APP_STYLESHEET: Final = f"""
/* ---------- Base ---------- */
QWidget {{
    color: {_P.TEXT};
    font-size: 13px;
}}
QMainWindow, QWidget#root, QWidget#mainArea {{
    background-color: {_P.BG};
}}
QToolTip {{
    background-color: {_P.ELEVATED};
    color: {_P.TEXT};
    border: 1px solid {_P.BORDER};
    border-radius: 4px;
    padding: 6px 8px;
}}

/* ---------- Sidebar ---------- */
QFrame#sidebar {{
    background-color: {_P.SURFACE};
    border-right: 1px solid {_P.BORDER};
}}
QScrollArea#sidebarScroll, QWidget#sidebarContent {{
    background: transparent;
    border: none;
}}
QLabel#brandTitle {{
    font-size: 15px;
    font-weight: 600;
}}
QLabel#brandCaption {{
    color: {_P.TEXT_SUBTLE};
    font-size: 11px;
}}
QLabel#sectionHeader {{
    color: {_P.TEXT_MUTED};
    font-size: 11px;
    font-weight: 700;
    letter-spacing: 0.4px;
}}
QLabel#fieldLabel {{
    color: {_P.TEXT};
    font-size: 12px;
}}
QLabel#statusBanner {{
    background-color: {_P.BG};
    border: 1px solid {_P.BORDER_MUTED};
    border-radius: 6px;
    padding: 8px 10px;
    color: {_P.TEXT_MUTED};
    font-size: 11px;
    line-height: 1.4;
}}
QFrame#storageFooter {{
    background-color: {_P.SURFACE};
    border-top: 1px solid {_P.BORDER_MUTED};
}}
QFrame#pathBox {{
    background-color: {_P.BG};
    border: 1px solid {_P.BORDER_MUTED};
    border-radius: 6px;
}}
QLabel#pathLabel {{
    color: {_P.TEXT_MUTED};
    font-family: {MONO_FONT_STACK};
    font-size: 11px;
    line-height: 1.3;
}}
QFrame#divider {{
    background-color: {_P.BORDER_MUTED};
    border: none;
    min-height: 1px;
    max-height: 1px;
}}

/* ---------- Inputs ---------- */
QLineEdit, QPlainTextEdit, QComboBox {{
    background-color: {_P.BG};
    border: 1px solid {_P.BORDER};
    border-radius: 6px;
    padding: 5px 8px;
    selection-background-color: {_P.ACCENT};
    selection-color: #ffffff;
}}
QSpinBox, QDoubleSpinBox {{
    background-color: {_P.BG};
    border: 1px solid {_P.BORDER};
    border-radius: 6px;
    padding: 3px 6px;
    padding-right: 20px;
    font-family: {MONO_FONT_STACK};
    font-size: 12px;
    selection-background-color: {_P.ACCENT};
    selection-color: #ffffff;
}}
QSpinBox::up-button, QDoubleSpinBox::up-button {{
    subcontrol-origin: border;
    subcontrol-position: top right;
    width: 18px;
    border-left: 1px solid {_P.BORDER_MUTED};
    border-bottom: 1px solid {_P.BORDER_MUTED};
    border-top-right-radius: 5px;
    background-color: {_P.SURFACE};
}}
QSpinBox::down-button, QDoubleSpinBox::down-button {{
    subcontrol-origin: border;
    subcontrol-position: bottom right;
    width: 18px;
    border-left: 1px solid {_P.BORDER_MUTED};
    border-bottom-right-radius: 5px;
    background-color: {_P.SURFACE};
}}
QSpinBox::up-button:hover, QDoubleSpinBox::up-button:hover,
QSpinBox::down-button:hover, QDoubleSpinBox::down-button:hover {{
    background-color: {_P.ELEVATED};
}}
QSpinBox::up-arrow, QDoubleSpinBox::up-arrow {{
    width: 7px;
    height: 7px;
}}
QSpinBox::down-arrow, QDoubleSpinBox::down-arrow {{
    width: 7px;
    height: 7px;
}}
QLineEdit:hover, QPlainTextEdit:hover, QComboBox:hover,
QSpinBox:hover, QDoubleSpinBox:hover {{
    border-color: {_P.BORDER_STRONG};
}}
QLineEdit:focus, QPlainTextEdit:focus, QComboBox:focus,
QSpinBox:focus, QDoubleSpinBox:focus {{
    border-color: {_P.ACCENT_HOVER};
}}
QLineEdit:disabled, QPlainTextEdit:disabled, QComboBox:disabled,
QSpinBox:disabled, QDoubleSpinBox:disabled {{
    color: {_P.TEXT_SUBTLE};
    background-color: {_P.SURFACE};
}}
QComboBox QAbstractItemView {{
    background-color: {_P.ELEVATED};
    border: 1px solid {_P.BORDER};
    padding: 4px;
    outline: 0;
    selection-background-color: {_P.ACCENT};
}}

/* ---------- Buttons ---------- */
QPushButton {{
    background-color: {_P.ELEVATED};
    color: {_P.TEXT};
    border: 1px solid {_P.BORDER};
    border-radius: 6px;
    padding: 6px 14px;
    font-weight: 500;
}}
QPushButton:hover {{
    background-color: {_P.BORDER};
    border-color: {_P.BORDER_STRONG};
}}
QPushButton:pressed {{
    background-color: #282e33;
}}
QPushButton:disabled {{
    color: {_P.TEXT_SUBTLE};
    background-color: {_P.SURFACE};
    border-color: {_P.BORDER_MUTED};
}}
QPushButton#primaryButton {{
    background-color: {_P.ACCENT};
    border: 1px solid rgba(240, 246, 252, 0.10);
    color: #ffffff;
}}
QPushButton#primaryButton:hover {{
    background-color: {_P.ACCENT_HOVER};
}}
QPushButton#primaryButton:pressed {{
    background-color: #1a5fd0;
}}
QPushButton#primaryButton:disabled {{
    background-color: #1c2d4a;
    color: #7d8590;
    border-color: transparent;
}}
QPushButton#dangerButton {{
    background-color: transparent;
    color: {_P.DANGER};
    border: 1px solid {_P.BORDER};
}}
QPushButton#dangerButton:hover {{
    background-color: rgba(248, 81, 73, 0.12);
    border-color: {_P.DANGER};
}}
QPushButton#linkButton {{
    background-color: transparent;
    border: none;
    color: {_P.ACCENT_TEXT};
    padding: 2px 4px;
}}
QPushButton#linkButton:hover {{
    color: {_P.TEXT};
}}

/* ---------- Header / chat / composer ---------- */
QFrame#header {{
    background-color: {_P.BG};
    border-bottom: 1px solid {_P.BORDER_MUTED};
}}
QLabel#headerTitle {{
    font-size: 14px;
    font-weight: 600;
}}
QTextBrowser#chatView {{
    background-color: {_P.BG};
    border: none;
}}
QFrame#composer {{
    background-color: {_P.SURFACE};
    border: 1px solid {_P.BORDER};
    border-radius: 12px;
}}
QFrame#composer[focused="true"] {{
    border-color: {_P.ACCENT_HOVER};
}}
QPlainTextEdit#composerInput {{
    background: transparent;
    border: none;
    padding: 2px 0px;
    font-size: 14px;
}}
QLabel#hint {{
    color: {_P.TEXT_SUBTLE};
    font-size: 11px;
}}

/* ---------- Progress ---------- */
QProgressBar#loadProgress {{
    background-color: {_P.BORDER_MUTED};
    border: none;
    border-radius: 1px;
    min-height: 3px;
    max-height: 3px;
}}
QProgressBar#loadProgress::chunk {{
    background-color: {_P.ACCENT_HOVER};
}}

/* ---------- Status bar ---------- */
QStatusBar {{
    background-color: {_P.SURFACE};
    border-top: 1px solid {_P.BORDER};
    color: {_P.TEXT_MUTED};
    font-size: 11px;
}}
QStatusBar::item {{
    border: none;
}}
QStatusBar QLabel {{
    color: {_P.TEXT_MUTED};
    font-size: 11px;
    padding: 0px 10px;
}}

/* ---------- Scrollbars ---------- */
QScrollBar:vertical {{
    background: transparent;
    width: 10px;
    margin: 0px;
}}
QScrollBar::handle:vertical {{
    background: {_P.BORDER};
    border-radius: 3px;
    min-height: 32px;
    margin: 2px;
}}
QScrollBar::handle:vertical:hover {{
    background: {_P.BORDER_STRONG};
}}
QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{
    height: 0px;
}}
QScrollBar::add-page:vertical, QScrollBar::sub-page:vertical {{
    background: none;
}}
"""

# Stylesheet applied to the QTextDocument behind the chat view. Qt rich text
# supports only a CSS2 subset, so keep selectors to tags and single classes.
CHAT_DOCUMENT_CSS: Final = f"""
body {{ color: {_P.TEXT}; font-family: {CHAT_FONT_STACK}; font-size: 14px; }}
p {{ margin-top: 0px; margin-bottom: 8px; line-height: 150%; }}
a {{ color: {_P.ACCENT_TEXT}; text-decoration: none; }}
h1 {{ font-size: 20px; font-weight: 600; margin-top: 12px; margin-bottom: 8px; }}
h2 {{ font-size: 17px; font-weight: 600; margin-top: 12px; margin-bottom: 6px; }}
h3 {{ font-size: 15px; font-weight: 600; margin-top: 10px; margin-bottom: 6px; }}
ul, ol {{ margin-top: 0px; margin-bottom: 8px; }}
li {{ margin-bottom: 4px; }}
code {{ font-family: {MONO_FONT_STACK}; font-size: 13px; background-color: {_P.ELEVATED}; color: {_P.INLINE_CODE}; }}
pre {{ font-family: {MONO_FONT_STACK}; font-size: 13px; background-color: {_P.CODE_BG}; margin-top: 4px; margin-bottom: 10px; }}
.block {{ background-color: {_P.CODE_BG}; color: {_P.TEXT}; }}
blockquote {{ color: {_P.TEXT_MUTED}; margin-left: 14px; }}
th {{ background-color: {_P.SURFACE}; font-weight: 600; }}
.role {{ font-weight: 600; margin-bottom: 4px; }}
.meta {{ color: {_P.TEXT_SUBTLE}; font-size: 12px; }}
.muted {{ color: {_P.TEXT_MUTED}; }}
.error {{ color: {_P.DANGER}; }}
.welcome-title {{ font-size: 24px; font-weight: 600; margin-bottom: 6px; }}
"""
