"""
Unit tests for SmolLM model worker and utilities.
"""

import pytest
import torch
from pathlib import Path
from model_worker import StopSignalCriteria, get_base_dir, get_default_models_dir, is_model_downloaded_locally
from app import PRESET_MODELS


def test_default_preset_model():
    # SmolLM2-1.7B-Instruct must be the first and default preset model
    assert PRESET_MODELS[0][1] == "HuggingFaceTB/SmolLM2-1.7B-Instruct"


def test_stop_signal_criteria():
    criteria = StopSignalCriteria()
    dummy_input_ids = torch.tensor([[1, 2, 3]])
    dummy_scores = torch.tensor([[0.1, 0.2]])

    assert not criteria(dummy_input_ids, dummy_scores)
    assert not criteria.stop_requested

    # Request stop
    criteria.request_stop()
    assert criteria.stop_requested
    assert criteria(dummy_input_ids, dummy_scores)


def test_preset_models():
    assert len(PRESET_MODELS) >= 5
    model_ids = [m[1] for m in PRESET_MODELS]
    assert "HuggingFaceTB/SmolLM2-1.7B-Instruct" in model_ids
    assert "HuggingFaceTB/SmolLM2-135M-Instruct" in model_ids
    assert "HuggingFaceTB/SmolLM3-3B" in model_ids
    assert "custom" in model_ids


def test_local_models_dir():
    base_dir = get_base_dir()
    models_dir = get_default_models_dir()
    assert models_dir == base_dir / "models"
    assert models_dir.exists()


def test_is_model_downloaded_locally(tmp_path: Path):
    model_id = "HuggingFaceTB/SmolLM2-1.7B-Instruct"
    assert not is_model_downloaded_locally(model_id, tmp_path)

    # Mock model download
    target = tmp_path / "SmolLM2-1.7B-Instruct"
    target.mkdir()
    (target / "config.json").write_text("{}")
    (target / "model.safetensors").write_bytes(b"dummy")

    assert is_model_downloaded_locally(model_id, tmp_path)


def test_plain_text_to_html():
    from chat_renderer import plain_text_to_html

    raw = "Hello & welcome <world>\nLine 2"
    result = plain_text_to_html(raw)
    assert "&amp;" in result
    assert "&lt;world&gt;" in result
    assert "<br>" in result
    assert "<p>" in result and "</p>" in result


def test_markdown_to_html():
    from chat_renderer import markdown_to_html

    md = "# Title\n\n```python\nprint('hi')\n```"
    html = markdown_to_html(md)
    assert "Title" in html
    assert '<pre><code class="block">' in html


def test_markdown_sanitization():
    from chat_renderer import markdown_to_html

    # Raw script or dangerous tag should not be passed through as executable HTML
    dangerous = '<script>alert("hack")</script>'
    html = markdown_to_html(dangerous)
    # The preprocessor deregistration ensures raw html blocks are escaped
    assert "<script>" not in html


def test_render_message_user_and_assistant():
    from chat_renderer import ChatMessage, render_message, STREAMING_CURSOR

    # User message (aligned right with bubble)
    msg_user = ChatMessage(role="user", content="Hello!")
    html_user = render_message(0, msg_user)
    assert "Hello!" in html_user
    assert "你" in html_user
    assert 'align="right"' in html_user

    # Assistant message (non-streaming, aligned left)
    msg_asst = ChatMessage(role="assistant", content="Hi there!", meta="25.4 tok/s")
    html_asst = render_message(1, msg_asst, streaming=False)
    assert "Hi there!" in html_asst
    assert "SmolLM" in html_asst
    assert "25.4 tok/s" in html_asst
    assert 'href="copy:1"' in html_asst
    assert '<td width="44" valign="top">' in html_asst

    # Assistant message (streaming)
    html_stream = render_message(1, msg_asst, streaming=True)
    assert STREAMING_CURSOR in html_stream


def test_render_welcome():
    from chat_renderer import render_welcome, SUGGESTIONS

    welcome = render_welcome("SmolLM2-1.7B-Instruct")
    assert "SmolLM2-1.7B-Instruct" in welcome
    assert "今天想聊些什麼？" in welcome
    for i, (title, _) in enumerate(SUGGESTIONS):
        assert f'href="prompt:{i}"' in welcome


def test_wrap_document():
    from chat_renderer import wrap_document

    doc = wrap_document("<p>Test</p>", width_px=700)
    assert 'width="700"' in doc
    assert "<p>Test</p>" in doc

