"""E4 (#127): Explicit failure feedback — PipelineResult.warnings, diarization/RAG/budget messages."""

from __future__ import annotations

from pathlib import Path
from types import SimpleNamespace
from unittest.mock import MagicMock, patch

import numpy as np
import pytest

from voiceforge.core.pipeline import (
    PipelineResult,
    _step2_diarization,
    _step2_rag,
)


def test_pipeline_result_has_warnings_field() -> None:
    """PipelineResult has warnings field (list) and defaults to empty."""
    r = PipelineResult(
        segments=[],
        transcript="",
        diar_segments=[],
        context="",
        transcript_redacted=None,
    )
    assert hasattr(r, "warnings")
    assert r.warnings == []


def test_pipeline_result_warnings_populated() -> None:
    """PipelineResult accepts explicit warnings list."""
    r = PipelineResult(
        segments=[],
        transcript="",
        diar_segments=[],
        context="",
        transcript_redacted=None,
        warnings=["⚠ Foo", "ℹ Bar"],
    )
    assert r.warnings == ["⚠ Foo", "ℹ Bar"]


def test_step2_diarization_returns_warnings_on_low_memory(monkeypatch: pytest.MonkeyPatch) -> None:
    """_step2_diarization returns (segments, warnings) with RAM message when available < 2GB."""
    import voiceforge.core.pipeline as pipeline_mod

    mock_vm = MagicMock()
    mock_vm.available = 1024**3  # 1 GB
    monkeypatch.setattr(pipeline_mod, "psutil", MagicMock(virtual_memory=lambda: mock_vm))

    audio_f = np.zeros(16000 * 5, dtype=np.float32)
    segments, warnings = _step2_diarization(audio_f, 16000, pyannote_restart_hours=2)

    assert segments == []
    assert len(warnings) == 1
    assert "Speaker" in warnings[0] or "RAM" in warnings[0] or "keyring" in warnings[0]


def test_step2_diarization_returns_warning_when_no_hf_token(monkeypatch: pytest.MonkeyPatch) -> None:
    """When HuggingFace token is missing, diarization returns empty segments and HF warning."""
    import voiceforge.core.pipeline as pipeline_mod

    mock_vm = MagicMock()
    mock_vm.available = 3 * 1024**3
    monkeypatch.setattr(pipeline_mod, "psutil", MagicMock(virtual_memory=lambda: mock_vm))

    try:
        import keyring

        monkeypatch.setattr(keyring, "get_password", lambda s, k: None)
    except ImportError:
        pytest.skip("keyring not installed")

    audio_f = np.zeros(16000 * 5, dtype=np.float32)
    segments, warnings = _step2_diarization(audio_f, 16000, pyannote_restart_hours=2)

    assert segments == []
    assert len(warnings) == 1
    assert "HuggingFace" in warnings[0] or "keyring" in warnings[0]


def test_step2_rag_returns_warning_when_no_db(tmp_path: Path) -> None:
    """_step2_rag returns (context, warnings, results); warns when RAG DB does not exist (KC5)."""
    rag_path = tmp_path / "nonexistent.db"
    context, warnings, results = _step2_rag("hello world", str(rag_path))

    assert context == ""
    assert results == []
    assert len(warnings) == 1
    assert "index" in warnings[0].lower() or "voiceforge" in warnings[0].lower()


def test_get_budget_warning_returns_none_when_under_80() -> None:
    """get_budget_warning_if_near_limit returns None when cost today < 80% of limit."""
    from voiceforge.llm.router import get_budget_warning_if_near_limit

    with patch("voiceforge.core.metrics.get_cost_today", return_value=0.10):
        cfg = SimpleNamespace(daily_budget_limit_usd=1.0)
        assert get_budget_warning_if_near_limit(cfg) is None


def test_get_budget_warning_returns_message_when_over_80() -> None:
    """get_budget_warning_if_near_limit returns i18n message when cost >= 80% of limit."""
    from voiceforge.llm.router import get_budget_warning_if_near_limit

    with patch("voiceforge.core.metrics.get_cost_today", return_value=0.90):
        cfg = SimpleNamespace(daily_budget_limit_usd=1.0)
        msg = get_budget_warning_if_near_limit(cfg)
        assert msg is not None
        assert "budget" in msg.lower() or "0.90" in msg or "1.00" in msg
