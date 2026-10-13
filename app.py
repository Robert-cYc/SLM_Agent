"""
SmolLM Studio - desktop chat client for local Hugging Face small language models.

Default model: SmolLM2-1.7B-Instruct, persisted under ./models next to the executable.
"""

import gc
import logging
import os
import subprocess
import sys
from pathlib import Path
from typing import Optional


def _ensure_std_streams() -> None:
    """Windowed PyInstaller builds have no console; give libraries (tqdm, logging) a sink."""
    for name in ("stdout", "stderr"):
        if getattr(sys, name) is None:
            setattr(sys, name, open(os.devnull, "w", encoding="utf-8"))


_ensure_std_streams()

# Heavy imports intentionally follow the stream guard above.
import torch  # noqa: E402
from PyQt6.QtCore import QTimer, QUrl  # noqa: E402
from PyQt6.QtGui import QCloseEvent, QDesktopServices, QFont, QKeySequence, QResizeEvent, QShortcut  # noqa: E402
from PyQt6.QtWidgets import (  # noqa: E402
    QApplication,
    QComboBox,
    QDoubleSpinBox,
    QFormLayout,
    QFrame,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMainWindow,
    QMessageBox,
    QPlainTextEdit,
    QProgressBar,
    QPushButton,
    QScrollArea,
    QSpinBox,
    QStatusBar,
    QTextBrowser,
    QVBoxLayout,
    QWidget,
)
from PyQt6.QtCore import Qt  # noqa: E402

from chat_renderer import SUGGESTIONS, ChatMessage, render_message, render_welcome, wrap_document  # noqa: E402
from model_worker import (  # noqa: E402
    ModelLoaderWorker,
    TextGeneratorWorker,
    get_base_dir,
    get_default_models_dir,
    is_model_downloaded_locally,
)
from styles import APP_STYLESHEET, CHAT_DOCUMENT_CSS, UI_FONT_FAMILY  # noqa: E402
from widgets import (  # noqa: E402
    ChatInputEdit,
    StatusIndicator,
    create_app_icon,
    make_divider,
    make_field_label,
    make_section_header,
)

logger = logging.getLogger(__name__)

APP_NAME = "SmolLM Studio"
APP_VERSION = "1.2.0"

PRESET_MODELS: list[tuple[str, str]] = [
    ("SmolLM2 1.7B Instruct  ·  3.4 GB  (預設)", "HuggingFaceTB/SmolLM2-1.7B-Instruct"),
    ("SmolLM2 360M Instruct  ·  720 MB", "HuggingFaceTB/SmolLM2-360M-Instruct"),
    ("SmolLM2 135M Instruct  ·  270 MB", "HuggingFaceTB/SmolLM2-135M-Instruct"),
    ("SmolLM3 3B  ·  6 GB", "HuggingFaceTB/SmolLM3-3B"),
    ("Qwen2.5 0.5B Instruct  ·  1 GB", "Qwen/Qwen2.5-0.5B-Instruct"),
    ("自訂 Hugging Face Repo ID…", "custom"),
]
DEFAULT_MODEL_ID = PRESET_MODELS[0][1]
DEFAULT_SYSTEM_PROMPT = "You are SmolLM, a helpful, accurate and concise AI assistant."

SIDEBAR_WIDTH_PX = 330
CHAT_MAX_WIDTH_PX = 820
CHAT_SIDE_PADDING_PX = 56
VRAM_REFRESH_MS = 2000


class MainWindow(QMainWindow):
    def __init__(self) -> None:
        super().__init__()
        self.setWindowTitle(APP_NAME)
        self.setWindowIcon(create_app_icon())
        self.resize(1240, 820)
        self.setMinimumSize(960, 640)

        self.models_dir = get_default_models_dir()
        self.tokenizer = None
        self.model = None
        self.loaded_model_id = ""
        self.device_summary = ""
        self.messages: list[ChatMessage] = []
        self._message_html: list[str] = []
        self.streaming_text: Optional[str] = None
        self._loading_model_id = ""
        self._is_loading = False
        self._stop_requested = False
        self.loader_worker: Optional[ModelLoaderWorker] = None
        self.gen_worker: Optional[TextGeneratorWorker] = None

        self._gpu_name = torch.cuda.get_device_name(0) if torch.cuda.is_available() else ""
        self._gpu_total_gb = (
            torch.cuda.get_device_properties(0).total_memory / 1024**3 if torch.cuda.is_available() else 0.0
        )

        self._resize_timer = QTimer(self, singleShot=True, interval=60)
        self._resize_timer.timeout.connect(self._refresh_chat)

        self._build_ui()
        self._build_status_bar()
        self._install_shortcuts()
        self._update_model_availability()
        self._set_session_state("idle")
        self._refresh_chat()

        self._vram_timer = QTimer(self, interval=VRAM_REFRESH_MS)
        self._vram_timer.timeout.connect(self._update_device_label)
        self._vram_timer.start()
        self._update_device_label()

        QTimer.singleShot(400, self._auto_load_default_model)

    # ------------------------------------------------------------------ UI
    def _build_ui(self) -> None:
        root = QWidget()
        root.setObjectName("root")
        layout = QHBoxLayout(root)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        layout.addWidget(self._build_sidebar())
        layout.addWidget(self._build_main_area(), 1)
        self.setCentralWidget(root)

    def _build_sidebar(self) -> QWidget:
        sidebar = QFrame()
        sidebar.setObjectName("sidebar")
        sidebar.setFixedWidth(SIDEBAR_WIDTH_PX)
        outer = QVBoxLayout(sidebar)
        outer.setContentsMargins(0, 0, 0, 0)
        outer.setSpacing(0)

        outer.addWidget(self._build_brand())
        outer.addWidget(make_divider())

        scroll = QScrollArea()
        scroll.setObjectName("sidebarScroll")
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.Shape.NoFrame)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        scroll.viewport().setAutoFillBackground(False)

        content = QWidget()
        content.setObjectName("sidebarContent")
        form = QVBoxLayout(content)
        form.setContentsMargins(18, 16, 18, 16)
        form.setSpacing(8)

        self._build_model_section(form)
        form.addSpacing(14)
        self._build_device_section(form)
        form.addSpacing(14)
        self._build_generation_section(form)
        form.addSpacing(14)
        form.addWidget(make_section_header("系統提示詞"))
        self.system_prompt_edit = QPlainTextEdit(DEFAULT_SYSTEM_PROMPT)
        self.system_prompt_edit.setFixedHeight(88)
        self.system_prompt_edit.setToolTip("每次對話開頭提供給模型的角色設定")
        form.addWidget(self.system_prompt_edit)
        form.addStretch(1)

        scroll.setWidget(content)
        outer.addWidget(scroll, 1)
        outer.addWidget(make_divider())
        outer.addWidget(self._build_storage_footer())
        return sidebar

    def _build_brand(self) -> QWidget:
        brand = QWidget()
        layout = QHBoxLayout(brand)
        layout.setContentsMargins(18, 16, 18, 14)
        layout.setSpacing(10)

        icon = QLabel()
        icon.setPixmap(create_app_icon().pixmap(30, 30))
        layout.addWidget(icon)

        texts = QVBoxLayout()
        texts.setSpacing(0)
        title = QLabel(APP_NAME)
        title.setObjectName("brandTitle")
        caption = QLabel(f"Local SLM Workbench  ·  v{APP_VERSION}")
        caption.setObjectName("brandCaption")
        texts.addWidget(title)
        texts.addWidget(caption)
        layout.addLayout(texts, 1)
        return brand

    def _build_model_section(self, form: QVBoxLayout) -> None:
        form.addWidget(make_section_header("模型"))

        self.model_combo = QComboBox()
        for label, model_id in PRESET_MODELS:
            self.model_combo.addItem(label, model_id)
        self.model_combo.currentIndexChanged.connect(self._on_model_selection_changed)
        form.addWidget(self.model_combo)

        self.custom_model_input = QLineEdit()
        self.custom_model_input.setPlaceholderText("organization/model-name")
        self.custom_model_input.setVisible(False)
        self.custom_model_input.textChanged.connect(self._update_model_availability)
        form.addWidget(self.custom_model_input)

        self.availability_indicator = StatusIndicator()
        form.addWidget(self.availability_indicator)

        self.load_button = QPushButton("載入模型")
        self.load_button.setObjectName("primaryButton")
        self.load_button.setMinimumHeight(34)
        self.load_button.setCursor(Qt.CursorShape.PointingHandCursor)
        self.load_button.clicked.connect(self.start_loading_model)
        form.addWidget(self.load_button)

        self.load_progress = QProgressBar()
        self.load_progress.setObjectName("loadProgress")
        self.load_progress.setRange(0, 0)
        self.load_progress.setTextVisible(False)
        self.load_progress.setVisible(False)
        form.addWidget(self.load_progress)

        self.load_detail = QLabel()
        self.load_detail.setObjectName("statusBanner")
        self.load_detail.setWordWrap(True)
        self.load_detail.setVisible(False)
        form.addWidget(self.load_detail)

    def _build_device_section(self, form: QVBoxLayout) -> None:
        form.addWidget(make_section_header("運算裝置"))
        self.device_combo = QComboBox()
        self.device_combo.addItem("自動（優先使用 GPU）", "Auto")
        self.device_combo.addItem("NVIDIA CUDA", "CUDA")
        self.device_combo.addItem("CPU", "CPU")
        form.addWidget(self.device_combo)

    def _build_generation_section(self, form: QVBoxLayout) -> None:
        form.addWidget(make_section_header("生成參數"))
        params = QFormLayout()
        params.setHorizontalSpacing(14)
        params.setVerticalSpacing(10)
        params.setLabelAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter)
        params.setFieldGrowthPolicy(QFormLayout.FieldGrowthPolicy.FieldsStayAtSizeHint)
        params.setRowWrapPolicy(QFormLayout.RowWrapPolicy.DontWrapRows)

        self.max_tokens_spin = QSpinBox()
        self.max_tokens_spin.setRange(32, 4096)
        self.max_tokens_spin.setSingleStep(64)
        self.max_tokens_spin.setValue(512)
        self.max_tokens_spin.setFixedWidth(86)
        self.max_tokens_spin.setAlignment(Qt.AlignmentFlag.AlignRight)
        params.addRow(make_field_label("最大長度", "單次回覆最多產生的 token 數"), self._wrap_field_right(self.max_tokens_spin))

        self.temp_spin = self._make_double_spin(0.0, 1.5, 0.05, 0.7)
        params.addRow(make_field_label("Temperature", "越高越有創意，越低越穩定；0 為貪婪解碼"), self._wrap_field_right(self.temp_spin))

        self.topp_spin = self._make_double_spin(0.1, 1.0, 0.05, 0.9)
        params.addRow(make_field_label("Top-P", "核取樣機率門檻"), self._wrap_field_right(self.topp_spin))

        self.rep_spin = self._make_double_spin(1.0, 2.0, 0.05, 1.15)
        params.addRow(make_field_label("重複懲罰", "抑制小模型重複輸出相同片語"), self._wrap_field_right(self.rep_spin))
        form.addLayout(params)

    @staticmethod
    def _wrap_field_right(widget: QWidget) -> QWidget:
        wrap = QWidget()
        layout = QHBoxLayout(wrap)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addStretch(1)
        layout.addWidget(widget)
        return wrap

    @staticmethod
    def _make_double_spin(minimum: float, maximum: float, step: float, value: float) -> QDoubleSpinBox:
        spin = QDoubleSpinBox()
        spin.setRange(minimum, maximum)
        spin.setSingleStep(step)
        spin.setDecimals(2)
        spin.setValue(value)
        spin.setFixedWidth(86)
        spin.setAlignment(Qt.AlignmentFlag.AlignRight)
        return spin

    def _build_storage_footer(self) -> QWidget:
        footer = QFrame()
        footer.setObjectName("storageFooter")
        layout = QVBoxLayout(footer)
        layout.setContentsMargins(18, 12, 18, 14)
        layout.setSpacing(6)

        top_row = QHBoxLayout()
        top_row.addWidget(make_section_header("模型存放目錄"))
        top_row.addStretch(1)

        open_button = QPushButton("📂 開啟")
        open_button.setObjectName("linkButton")
        open_button.setCursor(Qt.CursorShape.PointingHandCursor)
        open_button.clicked.connect(self.open_models_directory)
        top_row.addWidget(open_button)
        layout.addLayout(top_row)

        path_box = QFrame()
        path_box.setObjectName("pathBox")
        path_layout = QHBoxLayout(path_box)
        path_layout.setContentsMargins(8, 6, 8, 6)

        path_label = QLabel()
        path_label.setObjectName("pathLabel")
        path_label.setToolTip(str(self.models_dir))
        path_str = str(self.models_dir)
        path_label.setText(
            path_label.fontMetrics().elidedText(path_str, Qt.TextElideMode.ElideMiddle, 280)
        )
        path_layout.addWidget(path_label)
        layout.addWidget(path_box)
        return footer

    def _build_main_area(self) -> QWidget:
        main = QWidget()
        main.setObjectName("mainArea")
        layout = QVBoxLayout(main)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        layout.addWidget(self._build_header())

        self.chat_view = QTextBrowser()
        self.chat_view.setObjectName("chatView")
        self.chat_view.setOpenLinks(False)
        self.chat_view.anchorClicked.connect(self._on_anchor_clicked)
        self.chat_view.document().setDefaultStyleSheet(CHAT_DOCUMENT_CSS)
        self.chat_view.document().setDocumentMargin(20)
        layout.addWidget(self.chat_view, 1)

        layout.addLayout(self._build_composer())
        return main

    def _build_header(self) -> QWidget:
        header = QFrame()
        header.setObjectName("header")
        header.setFixedHeight(60)
        layout = QHBoxLayout(header)
        layout.setContentsMargins(24, 0, 16, 0)
        layout.setSpacing(12)

        titles = QVBoxLayout()
        titles.setSpacing(2)
        titles.setAlignment(Qt.AlignmentFlag.AlignVCenter)
        self.header_title = QLabel("尚未載入模型")
        self.header_title.setObjectName("headerTitle")
        self.session_indicator = StatusIndicator()
        titles.addWidget(self.header_title)
        titles.addWidget(self.session_indicator)
        layout.addLayout(titles)
        layout.addStretch(1)

        self.new_chat_button = QPushButton("新對話")
        self.new_chat_button.setToolTip("清除目前對話 (Ctrl+N)")
        self.new_chat_button.setCursor(Qt.CursorShape.PointingHandCursor)
        self.new_chat_button.clicked.connect(self.new_chat)
        layout.addWidget(self.new_chat_button)
        return header

    def _build_composer(self) -> QHBoxLayout:
        row = QHBoxLayout()
        row.setContentsMargins(24, 8, 24, 18)

        self.composer = QFrame()
        self.composer.setObjectName("composer")
        self.composer.setMaximumWidth(CHAT_MAX_WIDTH_PX + 40)
        layout = QVBoxLayout(self.composer)
        layout.setContentsMargins(14, 10, 10, 10)
        layout.setSpacing(6)

        self.input_edit = ChatInputEdit()
        self.input_edit.submitted.connect(self.send_message)
        self.input_edit.focus_changed.connect(self._on_composer_focus_changed)
        layout.addWidget(self.input_edit)

        actions = QHBoxLayout()
        actions.setSpacing(8)
        hint = QLabel("Enter 送出  ·  Shift+Enter 換行  ·  Esc 停止生成")
        hint.setObjectName("hint")
        actions.addWidget(hint)
        actions.addStretch(1)

        self.stop_button = QPushButton("停止")
        self.stop_button.setObjectName("dangerButton")
        self.stop_button.setCursor(Qt.CursorShape.PointingHandCursor)
        self.stop_button.clicked.connect(self.stop_generation)
        self.stop_button.setVisible(False)
        actions.addWidget(self.stop_button)

        self.send_button = QPushButton("送出")
        self.send_button.setObjectName("primaryButton")
        self.send_button.setCursor(Qt.CursorShape.PointingHandCursor)
        self.send_button.clicked.connect(self.send_message)
        actions.addWidget(self.send_button)
        layout.addLayout(actions)

        row.addStretch(1)
        row.addWidget(self.composer, 10)
        row.addStretch(1)
        return row

    def _build_status_bar(self) -> None:
        bar = QStatusBar()
        bar.setSizeGripEnabled(False)
        self.perf_label = QLabel("— tok/s")
        self.device_label = QLabel()
        bar.addPermanentWidget(self.perf_label)
        bar.addPermanentWidget(self.device_label)
        self.setStatusBar(bar)

    def _install_shortcuts(self) -> None:
        QShortcut(QKeySequence("Escape"), self, activated=self.stop_generation)
        QShortcut(QKeySequence("Ctrl+N"), self, activated=self.new_chat)

    # ------------------------------------------------------------- state
    @property
    def is_generating(self) -> bool:
        return self.gen_worker is not None and self.gen_worker.isRunning()

    def _selected_model_id(self) -> str:
        data = self.model_combo.currentData()
        return self.custom_model_input.text().strip() if data == "custom" else data

    @staticmethod
    def _short_name(model_id: str) -> str:
        return model_id.split("/")[-1] if model_id else ""

    def _on_model_selection_changed(self) -> None:
        is_custom = self.model_combo.currentData() == "custom"
        self.custom_model_input.setVisible(is_custom)
        if is_custom:
            self.custom_model_input.setFocus()
        self._update_model_availability()

    def _update_model_availability(self) -> None:
        model_id = self._selected_model_id()
        busy = self._is_loading or self.is_generating
        if not model_id:
            self.availability_indicator.set_state("idle", "請輸入 Hugging Face Repo ID")
            self.load_button.setEnabled(False)
            return

        self.load_button.setEnabled(not busy)
        if is_model_downloaded_locally(model_id, self.models_dir):
            self.availability_indicator.set_state("ready", "已下載 · 可離線載入")
            self.load_button.setText("載入模型")
        else:
            self.availability_indicator.set_state("remote", "尚未下載 · 首次載入將自動下載")
            self.load_button.setText("下載並載入")
        if self.model is not None and model_id == self.loaded_model_id:
            self.load_button.setText("重新載入")

    def _set_session_state(self, state: str) -> None:
        indicator = {
            "idle": ("idle", "未載入"),
            "loading": ("busy", "載入中…"),
            "ready": ("ready", f"就緒  ·  {self.device_summary}"),
            "generating": ("busy", "生成中…"),
            "error": ("error", "載入失敗"),
        }[state]
        self.session_indicator.set_state(*indicator)

        has_model = self.model is not None
        generating = state == "generating"
        busy = generating or state == "loading"
        self.send_button.setEnabled(has_model and not busy)
        self.send_button.setVisible(not generating)
        self.stop_button.setVisible(generating)
        self.new_chat_button.setEnabled(not generating)
        self.model_combo.setEnabled(not busy)
        self.custom_model_input.setEnabled(not busy)
        self.device_combo.setEnabled(not busy)
        self.input_edit.setPlaceholderText("輸入訊息…" if has_model else "請先從左側載入模型")
        self._update_model_availability()

    def _on_composer_focus_changed(self, focused: bool) -> None:
        self.composer.setProperty("focused", focused)
        self.composer.style().unpolish(self.composer)
        self.composer.style().polish(self.composer)

    def _update_device_label(self) -> None:
        if not self._gpu_name:
            self.device_label.setText("CPU 模式")
            return
        used_gb = torch.cuda.memory_allocated(0) / 1024**3
        self.device_label.setText(f"{self._gpu_name}  ·  VRAM {used_gb:.1f} / {self._gpu_total_gb:.1f} GB")

    # ---------------------------------------------------------- rendering
    def _content_width(self) -> int:
        available = self.chat_view.viewport().width() - CHAT_SIDE_PADDING_PX
        return max(360, min(CHAT_MAX_WIDTH_PX, available))

    def _refresh_chat(self, force_scroll: bool = False) -> None:
        if not self.messages and self.streaming_text is None:
            inner = render_welcome(self._short_name(self.loaded_model_id) if self.model else "")
        else:
            blocks = list(self._message_html)
            if self.streaming_text is not None:
                pending = ChatMessage("assistant", self.streaming_text)
                blocks.append(render_message(len(self.messages), pending, streaming=True))
            inner = "".join(blocks)

        scrollbar = self.chat_view.verticalScrollBar()
        previous = scrollbar.value()
        at_bottom = previous >= scrollbar.maximum() - 32
        self.chat_view.setHtml(wrap_document(inner, self._content_width()))
        scrollbar.setValue(scrollbar.maximum() if force_scroll or at_bottom else previous)

    def _append_message(self, message: ChatMessage) -> None:
        self.messages.append(message)
        self._message_html.append(render_message(len(self.messages) - 1, message))

    def resizeEvent(self, event: QResizeEvent) -> None:
        super().resizeEvent(event)
        self._resize_timer.start()

    def _on_anchor_clicked(self, url: QUrl) -> None:
        scheme = url.scheme()
        try:
            if scheme == "prompt":
                _, prompt = SUGGESTIONS[int(url.path())]
                self.input_edit.setPlainText(prompt)
                self.input_edit.moveCursor(self.input_edit.textCursor().MoveOperation.End)
                self.input_edit.setFocus()
            elif scheme == "copy":
                QApplication.clipboard().setText(self.messages[int(url.path())].content)
                self.statusBar().showMessage("已複製到剪貼簿", 2000)
            elif scheme in ("http", "https"):
                QDesktopServices.openUrl(url)
        except (ValueError, IndexError):
            logger.warning("Ignoring invalid chat link: %s", url.toString())

    # ------------------------------------------------------- model loading
    def _auto_load_default_model(self) -> None:
        if self.model is None and not self._is_loading and self._selected_model_id() == DEFAULT_MODEL_ID:
            if is_model_downloaded_locally(DEFAULT_MODEL_ID, self.models_dir):
                logger.info("Default model found locally; auto-loading.")
                self.start_loading_model()

    def _release_model(self) -> None:
        self.model = None
        self.tokenizer = None
        self.loaded_model_id = ""
        gc.collect()
        if torch.cuda.is_available():
            torch.cuda.empty_cache()

    def start_loading_model(self) -> None:
        model_id = self._selected_model_id()
        if not model_id:
            QMessageBox.warning(self, "缺少模型 ID", "請輸入 Hugging Face Repo ID，例如 HuggingFaceTB/SmolLM2-1.7B-Instruct")
            return
        if self._is_loading or self.is_generating:
            return

        self._release_model()
        self._is_loading = True
        self._loading_model_id = model_id
        self.load_progress.setVisible(True)
        self.load_detail.setVisible(True)
        self.load_detail.setText("準備中…")
        self.header_title.setText(self._short_name(model_id))
        self._set_session_state("loading")

        self.loader_worker = ModelLoaderWorker(model_id, self.device_combo.currentData(), self.models_dir)
        self.loader_worker.progress_signal.connect(self.load_detail.setText)
        self.loader_worker.finished_signal.connect(self._on_load_finished)
        self.loader_worker.start()

    def _on_load_finished(self, success: bool, message: str, tokenizer, model, local_path: str) -> None:
        self._is_loading = False
        self.load_progress.setVisible(False)

        if success:
            self.tokenizer, self.model = tokenizer, model
            self.loaded_model_id = self._loading_model_id
            param = next(model.parameters())
            self.device_summary = f"{param.device.type.upper()} · {str(param.dtype).replace('torch.', '')}"
            self.load_detail.setText(f"已從本機載入：{Path(local_path).name}")
            self.header_title.setText(self._short_name(self.loaded_model_id))
            self._set_session_state("ready")
            self.statusBar().showMessage(f"模型已載入：{self.loaded_model_id}", 5000)
            self._refresh_chat()
            self.input_edit.setFocus()
        else:
            logger.error("Model load failed: %s", message)
            self.load_detail.setText(message)
            self.header_title.setText("尚未載入模型")
            self._set_session_state("error")
            QMessageBox.critical(self, "模型載入失敗", message)
        self._update_device_label()

    def open_models_directory(self) -> None:
        try:
            if sys.platform.startswith("win"):
                os.startfile(str(self.models_dir))  # type: ignore[attr-defined]
            elif sys.platform == "darwin":
                subprocess.Popen(["open", str(self.models_dir)])
            else:
                subprocess.Popen(["xdg-open", str(self.models_dir)])
        except OSError as exc:
            logger.exception("Failed to open models directory")
            QMessageBox.warning(self, "無法開啟資料夾", str(exc))

    # ---------------------------------------------------------- generation
    def send_message(self) -> None:
        if self.model is None or self.tokenizer is None or self.is_generating or self._is_loading:
            return
        text = self.input_edit.toPlainText().strip()
        if not text:
            return

        self.input_edit.clear()
        self._append_message(ChatMessage("user", text))

        payload: list[dict[str, str]] = []
        system_prompt = self.system_prompt_edit.toPlainText().strip()
        if system_prompt:
            payload.append({"role": "system", "content": system_prompt})
        payload.extend(
            {"role": m.role, "content": m.content} for m in self.messages if m.role in ("user", "assistant")
        )

        self.streaming_text = ""
        self._stop_requested = False
        self.gen_worker = TextGeneratorWorker(
            tokenizer=self.tokenizer,
            model=self.model,
            messages=payload,
            max_new_tokens=self.max_tokens_spin.value(),
            temperature=self.temp_spin.value(),
            top_p=self.topp_spin.value(),
            repetition_penalty=self.rep_spin.value(),
        )
        self.gen_worker.token_signal.connect(self._on_token)
        self.gen_worker.finished_signal.connect(self._on_generation_finished)
        self.gen_worker.error_signal.connect(self._on_generation_error)
        self.gen_worker.start()
        self._set_session_state("generating")
        self._refresh_chat(force_scroll=True)

    def _on_token(self, token: str) -> None:
        if self.streaming_text is None:
            return
        self.streaming_text += token
        self._refresh_chat()

    def _on_generation_finished(self, full_response: str, elapsed: float, token_count: int) -> None:
        self.streaming_text = None
        speed = token_count / elapsed if elapsed > 0 else 0.0
        meta = f"{token_count} tokens  ·  {speed:.1f} tok/s  ·  {elapsed:.1f}s"
        if self._stop_requested:
            meta += "  ·  已中止"
        if full_response.strip():
            self._append_message(ChatMessage("assistant", full_response, meta))
        self.perf_label.setText(f"{speed:.1f} tok/s")
        self._set_session_state("ready")
        self._refresh_chat(force_scroll=True)
        self.input_edit.setFocus()

    def _on_generation_error(self, error_message: str) -> None:
        logger.error("Generation failed: %s", error_message)
        self.streaming_text = None
        self._append_message(ChatMessage("error", f"生成失敗：{error_message}"))
        self._set_session_state("ready")
        self._refresh_chat(force_scroll=True)

    def stop_generation(self) -> None:
        if self.is_generating and self.gen_worker is not None:
            self._stop_requested = True
            self.gen_worker.request_stop()
            self.statusBar().showMessage("正在停止生成…", 2000)

    def new_chat(self) -> None:
        if self.is_generating:
            return
        self.messages.clear()
        self._message_html.clear()
        self.perf_label.setText("— tok/s")
        self._refresh_chat()
        self.input_edit.setFocus()

    def closeEvent(self, event: QCloseEvent) -> None:
        if self.is_generating and self.gen_worker is not None:
            self.gen_worker.request_stop()
            self.gen_worker.wait(5000)
        if self.loader_worker is not None and self.loader_worker.isRunning():
            self.loader_worker.wait(5000)
        super().closeEvent(event)


def _configure_logging() -> None:
    log_dir = get_base_dir() / "logs"
    handlers: list[logging.Handler] = [logging.StreamHandler()]
    try:
        log_dir.mkdir(parents=True, exist_ok=True)
        handlers.append(logging.FileHandler(log_dir / "smollm_studio.log", encoding="utf-8"))
    except OSError:
        pass  # Read-only install location: fall back to stream logging only.
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(levelname)s %(name)s: %(message)s",
        handlers=handlers,
    )


def main() -> None:
    _configure_logging()
    app = QApplication(sys.argv)
    app.setApplicationName(APP_NAME)
    app.setApplicationVersion(APP_VERSION)
    app.setStyle("Fusion")
    app.setFont(QFont(UI_FONT_FAMILY, 10))
    app.setStyleSheet(APP_STYLESHEET)

    window = MainWindow()
    window.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
