"""
Unit tests for SmolLM model worker and utilities.
"""

import pytest
import torch
from model_worker import StopSignalCriteria
from app import PRESET_MODELS


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
    assert len(PRESET_MODELS) >= 4
    model_ids = [m[1] for m in PRESET_MODELS]
    assert "HuggingFaceTB/SmolLM2-135M-Instruct" in model_ids
    assert "HuggingFaceTB/SmolLM3-3B" in model_ids
    assert "custom" in model_ids


def test_messages_structure():
    messages = [
        {"role": "system", "content": "You are a test assistant."},
        {"role": "user", "content": "Hello!"},
    ]
    assert messages[0]["role"] == "system"
    assert messages[1]["content"] == "Hello!"
