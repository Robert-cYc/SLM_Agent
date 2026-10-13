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
