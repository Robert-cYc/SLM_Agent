"""
Modern Dark Theme QSS (Qt Style Sheets) for SmolLM Desktop Application.
"""

DARK_THEME = """
/* Global Window Style */
QMainWindow, QDialog {
    background-color: #0b0f19;
    color: #e2e8f0;
    font-family: "Segoe UI", "PingFang SC", "Microsoft YaHei", sans-serif;
}

QWidget {
    font-size: 13px;
    color: #e2e8f0;
}

/* ScrollBars */
QScrollBar:vertical {
    border: none;
    background: #0f172a;
    width: 8px;
    border-radius: 4px;
    margin: 0px 0px 0px 0px;
}
QScrollBar::handle:vertical {
    background: #334155;
    min-height: 25px;
    border-radius: 4px;
}
QScrollBar::handle:vertical:hover {
    background: #475569;
}
QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {
    height: 0px;
}

/* Panels and Cards */
QFrame#cardFrame {
    background-color: #131d31;
    border: 1px solid #1e293b;
    border-radius: 10px;
    padding: 10px;
}

QFrame#sidebarFrame {
    background-color: #0f172a;
    border-right: 1px solid #1e293b;
}

/* Labels */
QLabel {
    color: #cbd5e1;
}

QLabel#titleLabel {
    font-size: 17px;
    font-weight: 700;
    color: #f8fafc;
}

QLabel#subTitleLabel {
    font-size: 12px;
    color: #94a3b8;
}

QLabel#sectionTitle {
    font-size: 13px;
    font-weight: 600;
    color: #38bdf8;
    margin-top: 5px;
}

QLabel#statusBadge {
    padding: 4px 10px;
    border-radius: 12px;
    font-size: 11px;
    font-weight: 600;
}

/* Inputs and Combos */
QLineEdit, QComboBox, QPlainTextEdit, QSpinBox, QDoubleSpinBox {
    background-color: #1e293b;
    border: 1px solid #334155;
    border-radius: 6px;
    padding: 6px 10px;
    color: #f8fafc;
    selection-background-color: #3b82f6;
}

QLineEdit:focus, QComboBox:focus, QPlainTextEdit:focus, QSpinBox:focus, QDoubleSpinBox:focus {
    border: 1px solid #38bdf8;
    background-color: #1e293b;
}

QComboBox::drop-down {
    subcontrol-origin: padding;
    subcontrol-position: top right;
    width: 25px;
    border-left: 1px solid #334155;
}

QComboBox QAbstractItemView {
    background-color: #1e293b;
    border: 1px solid #334155;
    selection-background-color: #2563eb;
    color: #f8fafc;
    padding: 4px;
}

/* Buttons */
QPushButton {
    background-color: #2563eb;
    color: #ffffff;
    border: none;
    border-radius: 6px;
    padding: 7px 15px;
    font-weight: 600;
}

QPushButton:hover {
    background-color: #1d4ed8;
}

QPushButton:pressed {
    background-color: #1e40af;
}

QPushButton:disabled {
    background-color: #334155;
    color: #64748b;
}

QPushButton#secondaryButton {
    background-color: #1e293b;
    color: #cbd5e1;
    border: 1px solid #334155;
}

QPushButton#secondaryButton:hover {
    background-color: #334155;
    color: #f8fafc;
}

QPushButton#dangerButton {
    background-color: #dc2626;
    color: #ffffff;
}

QPushButton#dangerButton:hover {
    background-color: #b91c1c;
}

QPushButton#stopButton {
    background-color: #ef4444;
    color: #ffffff;
    font-weight: 600;
}

QPushButton#stopButton:hover {
    background-color: #dc2626;
}

/* Chat History Display */
QTextBrowser#chatBrowser {
    background-color: #0f172a;
    border: 1px solid #1e293b;
    border-radius: 10px;
    padding: 12px;
    color: #f1f5f9;
}

/* Sliders */
QSlider::groove:horizontal {
    height: 4px;
    background: #334155;
    border-radius: 2px;
}

QSlider::sub-page:horizontal {
    background: #38bdf8;
    border-radius: 2px;
}

QSlider::handle:horizontal {
    background: #f8fafc;
    border: 2px solid #38bdf8;
    width: 14px;
    margin-top: -5px;
    margin-bottom: -5px;
    border-radius: 7px;
}

QSlider::handle:horizontal:hover {
    background: #38bdf8;
}

/* Progress Bar */
QProgressBar {
    background-color: #1e293b;
    border: 1px solid #334155;
    border-radius: 4px;
    text-align: center;
    color: #f8fafc;
    font-size: 11px;
    height: 12px;
}

QProgressBar::chunk {
    background-color: #38bdf8;
    border-radius: 3px;
}
"""
