"""
Background workers for loading models and generating text streaming.
"""

import os
import time
import threading
from typing import List, Dict, Any, Optional

# Disable unnecessary warnings
os.environ["HF_HUB_DISABLE_SYMLINKS_WARNING"] = "1"

import torch
from PyQt6.QtCore import QThread, pyqtSignal
from transformers import (
    AutoTokenizer,
    AutoModelForCausalLM,
    TextIteratorStreamer,
    StoppingCriteria,
    StoppingCriteriaList,
)


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
    """Worker thread to download and initialize tokenizer and model."""

    progress_signal = pyqtSignal(str)
    finished_signal = pyqtSignal(bool, str, object, object)  # success, message, tokenizer, model

    def __init__(self, model_id: str, device_choice: str = "Auto"):
        super().__init__()
        self.model_id = model_id.strip()
        self.device_choice = device_choice

    def run(self):
        try:
            self.progress_signal.emit(f"Connecting to Hugging Face and fetching {self.model_id}...")

            # Determine device
            if self.device_choice == "CUDA" and torch.cuda.is_available():
                device = "cuda"
            elif self.device_choice == "CPU":
                device = "cpu"
            else:
                device = "cuda" if torch.cuda.is_available() else "cpu"

            # Load Tokenizer
            self.progress_signal.emit(f"Loading tokenizer for {self.model_id}...")
            tokenizer = AutoTokenizer.from_pretrained(
                self.model_id,
                trust_remote_code=True,
            )

            # Determine dtype
            if device == "cuda":
                # Check for bfloat16 capability or use float16
                dtype = torch.bfloat16 if torch.cuda.is_bf16_supported() else torch.float16
            else:
                dtype = torch.float32

            self.progress_signal.emit(f"Loading weights ({device.upper()} - {str(dtype).replace('torch.', '')})...")

            model = AutoModelForCausalLM.from_pretrained(
                self.model_id,
                dtype=dtype,
                low_cpu_mem_usage=True,
                trust_remote_code=True,
            )

            self.progress_signal.emit(f"Moving model to {device.upper()}...")
            model = model.to(device)
            model.eval()

            self.progress_signal.emit("Model loaded successfully!")
            self.finished_signal.emit(True, f"Model loaded on {device.upper()}", tokenizer, model)

        except Exception as e:
            err_msg = str(e)
            self.finished_signal.emit(False, f"Failed to load model: {err_msg}", None, None)


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
    ):
        super().__init__()
        self.tokenizer = tokenizer
        self.model = model
        self.messages = messages
        self.max_new_tokens = max_new_tokens
        self.temperature = temperature
        self.top_p = top_p
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
            }

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
