"""
Background workers for loading models and generating text streaming.
Supports downloading and persisting models locally next to the executable.
"""

import os
import sys
import time
import threading
from pathlib import Path
from typing import List, Dict, Any, Optional

# Disable unnecessary warnings
os.environ["HF_HUB_DISABLE_SYMLINKS_WARNING"] = "1"

import torch
from PyQt6.QtCore import QThread, pyqtSignal
from huggingface_hub import snapshot_download
from transformers import (
    AutoTokenizer,
    AutoModelForCausalLM,
    TextIteratorStreamer,
    StoppingCriteria,
    StoppingCriteriaList,
)


def get_base_dir() -> Path:
    """Get directory of the executable when frozen, or script directory."""
    if getattr(sys, "frozen", False):
        return Path(sys.executable).parent.resolve()
    try:
        return Path(__file__).parent.resolve()
    except NameError:
        return Path.cwd().resolve()


def get_default_models_dir() -> Path:
    """Get the models directory located right next to the executable / app."""
    models_dir = get_base_dir() / "models"
    models_dir.mkdir(parents=True, exist_ok=True)
    return models_dir


def is_model_downloaded_locally(model_id: str, models_dir: Optional[Path] = None) -> bool:
    """Check if model files are already downloaded in the local directory."""
    if not model_id or model_id == "custom":
        return False
    if models_dir is None:
        models_dir = get_default_models_dir()

    folder_name = model_id.strip().split("/")[-1]
    target_dir = models_dir / folder_name

    if not target_dir.exists() or not (target_dir / "config.json").exists():
        return False

    # Check for weights file
    has_weights = any(target_dir.glob("*.safetensors")) or any(target_dir.glob("*.bin"))
    return has_weights


class StopSignalCriteria(StoppingCriteria):
    """Custom StoppingCriteria to allow immediate interruption of text generation."""

    def __init__(self):
        super().__init__()
        self.stop_requested = False

    def request_stop(self):
        self.stop_requested = True

    def __call__(self, input_ids: torch.LongTensor, scores: torch.FloatTensor, **kwargs) -> bool:
        return self.stop_requested


class ModelLoaderWorker(QThread):
    """Worker thread to download and initialize tokenizer and model into local disk."""

    progress_signal = pyqtSignal(str)
    finished_signal = pyqtSignal(bool, str, object, object, str)  # success, message, tokenizer, model, local_path

    def __init__(self, model_id: str, device_choice: str = "Auto", models_dir: Optional[Path] = None):
        super().__init__()
        self.model_id = model_id.strip()
        self.device_choice = device_choice
        self.models_dir = models_dir or get_default_models_dir()

    def run(self):
        try:
            folder_name = self.model_id.split("/")[-1]
            local_model_path = self.models_dir / folder_name
            local_model_path.mkdir(parents=True, exist_ok=True)

            # Check if model is already stored locally
            already_downloaded = is_model_downloaded_locally(self.model_id, self.models_dir)

            if already_downloaded:
                self.progress_signal.emit(f"✓ 本地模型已就緒\n目錄：models/{local_model_path.name}\n正在載入至記憶體…")
            else:
                self.progress_signal.emit(f"⬇ 正在下載模型權重…\n{self.model_id}\n存放至：models/{local_model_path.name}")
                # Download to local directory directly
                snapshot_download(
                    repo_id=self.model_id,
                    local_dir=str(local_model_path),
                )
                self.progress_signal.emit(f"✓ 下載完成！\n模型已保存在：models/{local_model_path.name}")

            # Determine device
            if self.device_choice == "CUDA" and torch.cuda.is_available():
                device = "cuda"
            elif self.device_choice == "CPU":
                device = "cpu"
            else:
                device = "cuda" if torch.cuda.is_available() else "cpu"

            # Determine dtype
            if device == "cuda":
                dtype = torch.bfloat16 if torch.cuda.is_bf16_supported() else torch.float16
            else:
                dtype = torch.float32

            # Load Tokenizer from local directory
            self.progress_signal.emit("讀取 Tokenizer 分詞器...")
            tokenizer = AutoTokenizer.from_pretrained(
                str(local_model_path),
                local_files_only=True,
                trust_remote_code=True,
            )

            # Ensure pad_token exists
            if tokenizer.pad_token_id is None and tokenizer.eos_token_id is not None:
                tokenizer.pad_token_id = tokenizer.eos_token_id

            # Load Model from local directory
            self.progress_signal.emit(f"載入神經網路權重 ({device.upper()} - {str(dtype).replace('torch.', '')})...")
            model = AutoModelForCausalLM.from_pretrained(
                str(local_model_path),
                dtype=dtype,
                low_cpu_mem_usage=True,
                local_files_only=True,
                trust_remote_code=True,
            )

            self.progress_signal.emit(f"配置至運行裝置 {device.upper()}...")
            model = model.to(device)
            model.eval()

            self.progress_signal.emit("模型載入成功！")
            self.finished_signal.emit(True, f"本地模型已就緒 ({device.upper()})", tokenizer, model, str(local_model_path))

        except Exception as e:
            err_msg = str(e)
            self.finished_signal.emit(False, f"載入失敗: {err_msg}", None, None, "")


class TextGeneratorWorker(QThread):
    """Worker thread to stream generated text token by token."""

    token_signal = pyqtSignal(str)
    finished_signal = pyqtSignal(str, float, int)  # full_text, elapsed_sec, token_count
    error_signal = pyqtSignal(str)

    def __init__(
        self,
        tokenizer: Any,
        model: Any,
        messages: List[Dict[str, str]],
        max_new_tokens: int = 512,
        temperature: float = 0.7,
        top_p: float = 0.9,
        repetition_penalty: float = 1.15,
    ):
        super().__init__()
        self.tokenizer = tokenizer
        self.model = model
        self.messages = messages
        self.max_new_tokens = max_new_tokens
        self.temperature = temperature
        self.top_p = top_p
        self.repetition_penalty = repetition_penalty
        self.stop_criteria = StopSignalCriteria()

    def request_stop(self):
        """Called by UI to stop text generation cleanly."""
        self.stop_criteria.request_stop()

    def run(self):
        try:
            device = next(self.model.parameters()).device

            # Format chat prompt
            try:
                formatted_input = self.tokenizer.apply_chat_template(
                    self.messages,
                    tokenize=True,
                    add_generation_prompt=True,
                    return_tensors="pt",
                    return_dict=True,
                )
            except Exception:
                # Fallback if chat template is missing or fails
                raw_prompt = "\n".join([f"{m['role'].upper()}: {m['content']}" for m in self.messages]) + "\nASSISTANT:"
                formatted_input = self.tokenizer(raw_prompt, return_tensors="pt")

            inputs = {k: v.to(device) for k, v in formatted_input.items()}

            streamer = TextIteratorStreamer(
                self.tokenizer,
                skip_prompt=True,
                skip_special_tokens=True,
            )

            stopping_list = StoppingCriteriaList([self.stop_criteria])

            gen_kwargs = {
                **inputs,
                "streamer": streamer,
                "max_new_tokens": self.max_new_tokens,
                "stopping_criteria": stopping_list,
                "repetition_penalty": float(self.repetition_penalty),
            }

            if self.tokenizer.pad_token_id is not None:
                gen_kwargs["pad_token_id"] = self.tokenizer.pad_token_id
            if self.tokenizer.eos_token_id is not None:
                gen_kwargs["eos_token_id"] = self.tokenizer.eos_token_id

            if self.temperature > 0.05:
                gen_kwargs["do_sample"] = True
                gen_kwargs["temperature"] = float(self.temperature)
                gen_kwargs["top_p"] = float(self.top_p)
            else:
                gen_kwargs["do_sample"] = False

            # Run generation in a sub-thread so streamer can consume tokens in current thread
            gen_thread = threading.Thread(target=self.model.generate, kwargs=gen_kwargs)
            gen_thread.start()

            full_text = []
            token_count = 0
            start_time = time.time()

            for token in streamer:
                if self.stop_criteria.stop_requested:
                    break
                full_text.append(token)
                token_count += 1
                self.token_signal.emit(token)

            gen_thread.join(timeout=3.0)
            elapsed = time.time() - start_time
            full_response = "".join(full_text)

            self.finished_signal.emit(full_response, elapsed, token_count)

        except Exception as e:
            self.error_signal.emit(str(e))
