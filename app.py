"""
SmolLM Desktop AI Assistant - Modern PyQt6 GUI
"""

import sys
import os
import html
import torch

from PyQt6.QtWidgets import (
    QApplication,
    QMainWindow,
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QComboBox,
    QLineEdit,
    QPlainTextEdit,
    QTextBrowser,
    QSlider,
    QDoubleSpinBox,
    QSpinBox,
    QFrame,
    QSplitter,
    QMessageBox,
    QProgressBar,
)
from PyQt6.QtCore import Qt, QTimer
from PyQt6.QtGui import QFont, QKeyEvent

from styles import DARK_THEME
from model_worker import ModelLoaderWorker, TextGeneratorWorker

PRESET_MODELS = [
    ("HuggingFaceTB/SmolLM2-135M-Instruct (超輕量 135M / ~270MB)", "HuggingFaceTB/SmolLM2-135M-Instruct"),
    ("HuggingFaceTB/SmolLM2-360M-Instruct (輕量 360M / ~720MB)", "HuggingFaceTB/SmolLM2-360M-Instruct"),
    ("HuggingFaceTB/SmolLM2-1.7B-Instruct (高品質 1.7B / ~3.4GB)", "HuggingFaceTB/SmolLM2-1.7B-Instruct"),
    ("HuggingFaceTB/SmolLM3-3B (最新 SmolLM3 3B / ~6GB)", "HuggingFaceTB/SmolLM3-3B"),
    ("Qwen/Qwen2.5-0.5B-Instruct (阿里千問 0.5B / ~1GB)", "Qwen/Qwen2.5-0.5B-Instruct"),
    ("自訂模型 (Custom Hugging Face Repo ID)", "custom"),
]


class ChatInputEdit(QPlainTextEdit):
    """Text edit that submits on Enter and inserts newline on Shift+Enter."""

    def __init__(self, submit_callback, parent=None):
        super().__init__(parent)
        self.submit_callback = submit_callback

    def keyPressEvent(self, event: QKeyEvent):
        if event.key() in (Qt.Key.Key_Return, Qt.Key.Key_Enter):
            if event.modifiers() & Qt.KeyboardModifier.ShiftModifier:
                super().keyPressEvent(event)
            else:
                self.submit_callback()
        else:
            super().keyPressEvent(event)


class SmolLMAssistantWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("SmolLM AI Assistant - Hugging Face Desktop")
        self.resize(1100, 780)
        self.setMinimumSize(850, 600)

        # Model state
        self.tokenizer = None
        self.model = None
        self.current_model_id = ""
        self.conversation_history = []
        self.current_assistant_text = ""
        self.loader_worker = None
        self.gen_worker = None

        self.init_ui()
        self.detect_hardware()

    def init_ui(self):
        # Central widget and main horizontal layout
        central_widget = QWidget(self)
        self.setCentralWidget(central_widget)
        main_layout = QHBoxLayout(central_widget)
        main_layout.setContentsMargins(14, 14, 14, 14)
        main_layout.setSpacing(14)

        # Splitter to allow resizing sidebar vs chat area
        splitter = QSplitter(Qt.Orientation.Horizontal)
        splitter.setHandleWidth(4)

        # 1. Left Sidebar: Settings & Model Management
        sidebar = self.create_sidebar()
        splitter.addWidget(sidebar)

        # 2. Right Main Area: Chat Window
        chat_area = self.create_chat_area()
        splitter.addWidget(chat_area)

        # Set proportion: 320px sidebar, rest for chat
        splitter.setSizes([320, 780])
        splitter.setCollapsible(0, False)
        splitter.setCollapsible(1, False)

        main_layout.addWidget(splitter)

    def create_sidebar(self) -> QWidget:
        sidebar = QFrame()
        sidebar.setObjectName("sidebarFrame")
        layout = QVBoxLayout(sidebar)
        layout.setContentsMargins(12, 12, 12, 12)
        layout.setSpacing(12)

        # App Title Header
        title_box = QVBoxLayout()
        title = QLabel("🤖 SmolLM Studio")
        title.setObjectName("titleLabel")
        subtitle = QLabel("Local Hugging Face SLM GUI")
        subtitle.setObjectName("subTitleLabel")
        title_box.addWidget(title)
        title_box.addWidget(subtitle)
        layout.addLayout(title_box)

        # Separator line
        line = QFrame()
        line.setFrameShape(QFrame.Shape.HLine)
        line.setStyleSheet("background-color: #1e293b; max-height: 1px;")
        layout.addWidget(line)

        # Model Selection Card
        model_card = QFrame()
        model_card.setObjectName("cardFrame")
        mc_layout = QVBoxLayout(model_card)
        mc_layout.setSpacing(8)

        m_label = QLabel("模型選擇 (Model)")
        m_label.setObjectName("sectionTitle")
        mc_layout.addWidget(m_label)

        self.model_combo = QComboBox()
        for label, val in PRESET_MODELS:
            self.model_combo.addItem(label, val)
        self.model_combo.currentIndexChanged.connect(self.on_model_changed)
        mc_layout.addWidget(self.model_combo)

        # Custom Model ID input
        self.custom_model_input = QLineEdit()
        self.custom_model_input.setPlaceholderText("例如: HuggingFaceTB/SmolLM3-3B")
        self.custom_model_input.setVisible(False)
        mc_layout.addWidget(self.custom_model_input)

        # Hardware Device
        dev_label = QLabel("運行裝置 (Hardware Device)")
        dev_label.setObjectName("sectionTitle")
        mc_layout.addWidget(dev_label)

        self.device_combo = QComboBox()
        self.device_combo.addItem("自動檢測 (Auto: GPU優先)", "Auto")
        self.device_combo.addItem("NVIDIA CUDA (GPU 加速)", "CUDA")
        self.device_combo.addItem("CPU 處理器 (純 CPU)", "CPU")
        mc_layout.addWidget(self.device_combo)

        # Load Button
        self.load_model_btn = QPushButton("🚀 下載並載入模型")
        self.load_model_btn.setFixedHeight(36)
        self.load_model_btn.clicked.connect(self.start_loading_model)
        mc_layout.addWidget(self.load_model_btn)

        # Progress bar
        self.load_progress_bar = QProgressBar()
        self.load_progress_bar.setVisible(False)
        self.load_progress_bar.setRange(0, 0)  # Indeterminate animation
        mc_layout.addWidget(self.load_progress_bar)

        # Loading Status label
        self.load_status_label = QLabel("狀態: 尚未載入模型")
        self.load_status_label.setStyleSheet("color: #94a3b8; font-size: 11px;")
        self.load_status_label.setWordWrap(True)
        mc_layout.addWidget(self.load_status_label)

        layout.addWidget(model_card)

        # Parameters Card
        param_card = QFrame()
        param_card.setObjectName("cardFrame")
        p_layout = QVBoxLayout(param_card)
        p_layout.setSpacing(10)

        p_title = QLabel("推論參數 (Inference Config)")
        p_title.setObjectName("sectionTitle")
        p_layout.addWidget(p_title)

        # Max New Tokens
        tokens_box = QHBoxLayout()
        tokens_box.addWidget(QLabel("最大長度 (Max Tokens):"))
        self.max_tokens_spin = QSpinBox()
        self.max_tokens_spin.setRange(32, 4096)
        self.max_tokens_spin.setValue(512)
        self.max_tokens_spin.setSingleStep(64)
        tokens_box.addWidget(self.max_tokens_spin)
        p_layout.addLayout(tokens_box)

        # Temperature
        temp_box = QHBoxLayout()
        temp_box.addWidget(QLabel("創意度 (Temperature):"))
        self.temp_spin = QDoubleSpinBox()
        self.temp_spin.setRange(0.0, 1.5)
        self.temp_spin.setValue(0.7)
        self.temp_spin.setSingleStep(0.05)
        temp_box.addWidget(self.temp_spin)
        p_layout.addLayout(temp_box)

        # Top-P
        topp_box = QHBoxLayout()
        topp_box.addWidget(QLabel("取樣核心 (Top-P):"))
        self.topp_spin = QDoubleSpinBox()
        self.topp_spin.setRange(0.1, 1.0)
        self.topp_spin.setValue(0.9)
        self.topp_spin.setSingleStep(0.05)
        topp_box.addWidget(self.topp_spin)
        p_layout.addLayout(topp_box)

        # System Prompt
        sys_label = QLabel("系統提示詞 (System Prompt):")
        p_layout.addWidget(sys_label)
        self.system_prompt_edit = QPlainTextEdit()
        self.system_prompt_edit.setFixedHeight(70)
        self.system_prompt_edit.setPlainText(
            "You are a helpful and intelligent AI assistant. Answer clearly and concisely."
        )
        p_layout.addWidget(self.system_prompt_edit)

        layout.addWidget(param_card)

        # Hardware Info Card
        self.hardware_card = QFrame()
        self.hardware_card.setObjectName("cardFrame")
        hw_layout = QVBoxLayout(self.hardware_card)
        self.hw_label = QLabel("硬體狀態檢測中...")
        self.hw_label.setStyleSheet("color: #38bdf8; font-size: 11px;")
        self.hw_label.setWordWrap(True)
        hw_layout.addWidget(self.hw_label)
        layout.addWidget(self.hardware_card)

        layout.addStretch()
        return sidebar

    def create_chat_area(self) -> QWidget:
        chat_container = QWidget()
        layout = QVBoxLayout(chat_container)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(10)

        # Top status banner
        top_bar = QHBoxLayout()
        self.chat_header_status = QLabel("⚪ 未載入模型，請先在左側點選「下載並載入模型」")
        self.chat_header_status.setStyleSheet("color: #94a3b8; font-weight: 500;")
        top_bar.addWidget(self.chat_header_status)

        top_bar.addStretch()

        self.clear_btn = QPushButton("🗑️ 清空對話")
        self.clear_btn.setObjectName("secondaryButton")
        self.clear_btn.clicked.connect(self.clear_chat)
        top_bar.addWidget(self.clear_btn)

        layout.addLayout(top_bar)

        # Chat History Browser
        self.chat_browser = QTextBrowser()
        self.chat_browser.setObjectName("chatBrowser")
        self.chat_browser.setOpenExternalLinks(True)
        layout.addWidget(self.chat_browser, stretch=1)

        # Input Area Card
        input_card = QFrame()
        input_card.setObjectName("cardFrame")
        ic_layout = QVBoxLayout(input_card)
        ic_layout.setContentsMargins(10, 10, 10, 10)
        ic_layout.setSpacing(8)

        # Multi-line input edit
        self.input_edit = ChatInputEdit(self.send_message)
        self.input_edit.setFixedHeight(75)
        self.input_edit.setPlaceholderText("請輸入問題... (按 Enter 發送，Shift + Enter 換行)")
        ic_layout.addWidget(self.input_edit)

        # Action Buttons
        btn_bar = QHBoxLayout()

        self.speed_label = QLabel("")
        self.speed_label.setStyleSheet("color: #38bdf8; font-size: 11px;")
        btn_bar.addWidget(self.speed_label)

        btn_bar.addStretch()

        self.stop_btn = QPushButton("🛑 停止生成")
        self.stop_btn.setObjectName("stopButton")
        self.stop_btn.setEnabled(False)
        self.stop_btn.clicked.connect(self.stop_generation)
        btn_bar.addWidget(self.stop_btn)

        self.send_btn = QPushButton("💬 發送 (Send)")
        self.send_btn.setFixedHeight(34)
        self.send_btn.clicked.connect(self.send_message)
        btn_bar.addWidget(self.send_btn)

        ic_layout.addLayout(btn_bar)
        layout.addWidget(input_card)

        # Render initial greeting
        self.render_initial_welcome()
        return chat_container

    def detect_hardware(self):
        """Detect GPU and CPU capabilities."""
        if torch.cuda.is_available():
            gpu_name = torch.cuda.get_device_name(0)
            vram_gb = round(torch.cuda.get_device_properties(0).total_memory / (1024**3), 1)
            self.hw_label.setText(f"⚡ GPU: {gpu_name}\n💾 VRAM: {vram_gb} GB (CUDA 加速就緒)")
        else:
            self.hw_label.setText("💻 使用 CPU 模式 (未檢測到 CUDA GPU)")

    def on_model_changed(self):
        selected_data = self.model_combo.currentData()
        self.custom_model_input.setVisible(selected_data == "custom")

    def render_initial_welcome(self):
        welcome_html = """
        <div style="text-align: center; margin-top: 40px; margin-bottom: 20px;">
            <h2 style="color: #38bdf8; margin-bottom: 6px;">歡迎使用 SmolLM 本地小語言模型對話工具</h2>
            <p style="color: #94a3b8; font-size: 13px;">
                本程式由 Hugging Face Transformers 與 PyTorch 本地驅動，具備隱私、免聯網推論與 GPU 加速能力。
            </p>
            <div style="background-color: #1e293b; border: 1px solid #334155; border-radius: 8px; padding: 15px; margin: 20px auto; max-width: 620px; text-align: left;">
                <b style="color: #f8fafc;">💡 快速開始指南：</b><br>
                <ol style="color: #cbd5e1; margin-top: 8px; line-height: 1.8;">
                    <li>在左側選擇想體驗的模型（推薦初次使用 <b>SmolLM2-135M-Instruct</b>，僅 ~270MB，數秒內即可載入完畢；亦可選擇最新 <b>SmolLM3-3B</b>）。</li>
                    <li>點選 <b>「下載並載入模型」</b>（模型權重會自動下載並快取在本地）。</li>
                    <li>載入完成後即可在下方輸入問題進行問答，支援即時流式 Token 輸出與中途停止！</li>
                </ol>
            </div>
        </div>
        """
        self.chat_browser.setHtml(welcome_html)

    def append_message_to_html(self, role: str, text: str, is_partial: bool = False):
        """Append or update a chat bubble in the chat browser."""
        safe_text = html.escape(text).replace("\n", "<br>")

        if role == "user":
            bubble_html = f"""
            <div style="display: flex; justify-content: flex-end; margin: 12px 0;">
                <div style="background: linear-gradient(135deg, #2563eb, #1d4ed8); color: #ffffff; padding: 10px 16px; border-radius: 12px; max-width: 80%; box-shadow: 0 2px 4px rgba(0,0,0,0.2);">
                    <div style="font-weight: bold; font-size: 11px; margin-bottom: 4px; color: #bfdbfe;">👤 提問者 (You)</div>
                    <div style="font-size: 13px; line-height: 1.5;">{safe_text}</div>
                </div>
            </div>
            """
            self.chat_browser.append(bubble_html)

        elif role == "assistant":
            if is_partial:
                # Update partial assistant response in real time
                self.chat_browser.moveCursor(self.chat_browser.textCursor().MoveOperation.End)
                # Overwrite or append token
                self.chat_browser.insertPlainText(text)
            else:
                bubble_html = f"""
                <div style="display: flex; justify-content: flex-start; margin: 12px 0;">
                    <div style="background-color: #1e293b; border: 1px solid #334155; color: #f8fafc; padding: 12px 16px; border-radius: 12px; max-width: 85%;">
                        <div style="font-weight: bold; font-size: 11px; margin-bottom: 5px; color: #38bdf8;">🤖 SmolLM 助手</div>
                        <div style="font-size: 13px; line-height: 1.6;">{safe_text}</div>
                    </div>
                </div>
                """
                self.chat_browser.append(bubble_html)

        # Scroll to bottom
        sb = self.chat_browser.verticalScrollBar()
        sb.setValue(sb.maximum())

    def start_loading_model(self):
        selected_data = self.model_combo.currentData()
        if selected_data == "custom":
            model_id = self.custom_model_input.text().strip()
            if not model_id:
                QMessageBox.warning(self, "請輸入模型 ID", "請在輸入框中輸入 Hugging Face 倉庫 ID，例如 HuggingFaceTB/SmolLM3-3B")
                return
        else:
            model_id = selected_data

        device_choice = self.device_combo.currentData()

        # UI state during load
        self.load_model_btn.setEnabled(False)
        self.load_progress_bar.setVisible(True)
        self.load_status_label.setText(f"正在下載/載入 {model_id}...")
        self.chat_header_status.setText(f"⏳ 正在載入模型: {model_id}，請稍候...")

        # Worker
        self.loader_worker = ModelLoaderWorker(model_id, device_choice)
        self.loader_worker.progress_signal.connect(self.on_load_progress)
        self.loader_worker.finished_signal.connect(self.on_load_finished)
        self.loader_worker.start()

    def on_load_progress(self, msg: str):
        self.load_status_label.setText(msg)

    def on_load_finished(self, success: bool, message: str, tokenizer, model):
        self.load_model_btn.setEnabled(True)
        self.load_progress_bar.setVisible(False)

        if success:
            self.tokenizer = tokenizer
            self.model = model
            selected_data = self.model_combo.currentData()
            self.current_model_id = self.custom_model_input.text().strip() if selected_data == "custom" else selected_data

            self.load_status_label.setText(f"✅ {message}")
            self.chat_header_status.setText(f"🟢 已就緒: {self.current_model_id} ({message})")

            # Update hardware card with current memory
            if torch.cuda.is_available() and next(model.parameters()).is_cuda:
                allocated = round(torch.cuda.memory_allocated(0) / (1024**3), 2)
                self.hw_label.setText(f"⚡ GPU: {torch.cuda.get_device_name(0)}\n📊 模型佔用 VRAM: {allocated} GB")

            QMessageBox.information(self, "模型載入完成", f"模型 {self.current_model_id} 已成功載入並可以使用！")
        else:
            self.load_status_label.setText("❌ 載入失敗")
            self.chat_header_status.setText("🔴 模型載入失敗")
            QMessageBox.critical(self, "模型載入失敗", f"無法載入模型，錯誤訊息：\n{message}")

    def send_message(self):
        if self.model is None or self.tokenizer is None:
            QMessageBox.warning(self, "模型尚未載入", "請先點選左側面板的「🚀 下載並載入模型」以載入語言模型！")
            return

        user_text = self.input_edit.toPlainText().strip()
        if not user_text:
            return

        self.input_edit.clear()

        # Add user message to UI
        self.append_message_to_html("user", user_text)

        # Build messages payload
        messages = []
        sys_prompt = self.system_prompt_edit.toPlainText().strip()
        if sys_prompt:
            messages.append({"role": "system", "content": sys_prompt})

        for msg in self.conversation_history:
            messages.append(msg)

        messages.append({"role": "user", "content": user_text})

        # Append assistant header
        start_assistant_html = """
        <div style="margin: 12px 0;">
            <div style="background-color: #1e293b; border: 1px solid #334155; color: #f8fafc; padding: 12px 16px; border-radius: 12px; max-width: 88%;">
                <div style="font-weight: bold; font-size: 11px; margin-bottom: 5px; color: #38bdf8;">🤖 SmolLM 助手</div>
                <div id="current_stream_response" style="font-size: 13px; line-height: 1.6; white-space: pre-wrap;">
        """
        self.chat_browser.append(start_assistant_html)

        # UI buttons state
        self.send_btn.setEnabled(False)
        self.stop_btn.setEnabled(True)
        self.speed_label.setText("⚡ 正在思考中...")

        self.current_assistant_text = ""

        # Launch generation worker
        self.gen_worker = TextGeneratorWorker(
            tokenizer=self.tokenizer,
            model=self.model,
            messages=messages,
            max_new_tokens=self.max_tokens_spin.value(),
            temperature=self.temp_spin.value(),
            top_p=self.topp_spin.value(),
        )
        self.gen_worker.token_signal.connect(self.on_token_received)
        self.gen_worker.finished_signal.connect(lambda full, elapsed, count: self.on_generation_finished(user_text, full, elapsed, count))
        self.gen_worker.error_signal.connect(self.on_generation_error)
        self.gen_worker.start()

    def on_token_received(self, token: str):
        self.current_assistant_text += token
        self.chat_browser.moveCursor(self.chat_browser.textCursor().MoveOperation.End)
        self.chat_browser.insertPlainText(token)
        sb = self.chat_browser.verticalScrollBar()
        sb.setValue(sb.maximum())

    def on_generation_finished(self, user_text: str, full_response: str, elapsed: float, token_count: int):
        # Close HTML block
        close_html = "</div></div></div>"
        self.chat_browser.append(close_html)

        # Update history
        self.conversation_history.append({"role": "user", "content": user_text})
        self.conversation_history.append({"role": "assistant", "content": full_response})

        # Calculate speed
        speed = round(token_count / elapsed, 1) if elapsed > 0 else 0
        self.speed_label.setText(f"⚡ 推論速度: {speed} tokens/s ({token_count} 字元 / {round(elapsed, 2)}秒)")

        self.send_btn.setEnabled(True)
        self.stop_btn.setEnabled(False)

    def on_generation_error(self, err_msg: str):
        self.chat_browser.append(f"<div style='color: #ef4444;'>❌ 生成過程中發生錯誤: {html.escape(err_msg)}</div></div></div>")
        self.send_btn.setEnabled(True)
        self.stop_btn.setEnabled(False)
        self.speed_label.setText("")

    def stop_generation(self):
        if self.gen_worker and self.gen_worker.isRunning():
            self.gen_worker.request_stop()
            self.speed_label.setText("🛑 使用者中止生成")

    def clear_chat(self):
        self.conversation_history.clear()
        self.render_initial_welcome()
        self.speed_label.setText("")


def main():
    app = QApplication(sys.argv)
    app.setStyleSheet(DARK_THEME)

    # Set default application font
    font = QFont("Segoe UI", 10)
    app.setFont(font)

    window = SmolLMAssistantWindow()
    window.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
