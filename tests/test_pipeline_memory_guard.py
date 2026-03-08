"""Tests for pipeline diarization memory guard (#37): low-memory skip and OOM fallback."""

from __future__ import annotations

from unittest.mock import MagicMock

import numpy as np
import pytest

from voiceforge.core.pipeline import (
    MIN_AVAILABLE_FOR_DIARIZATION_BYTES,
    _step2_diarization,
)


def test_diarization_skipped_when_low_memory(monkeypatch: pytest.MonkeyPatch) -> None:
    """When psutil.virtual_memory().available < 2GB, diarization is skipped and [] returned."""
    import voiceforge.core.pipeline as pipeline_mod

    mock_vm = MagicMock()
    mock_vm.available = 1024**3  # 1 GB
    monkeypatch.setattr(pipeline_mod, "psutil", MagicMock(virtual_memory=lambda: mock_vm))

    audio_f = np.zeros(16000 * 10, dtype=np.float32)  # 10 s
    segments, warnings = _step2_diarization(audio_f, 16000, pyannote_restart_hours=2)

    assert segments == []
    assert len(warnings) == 1
    assert "RAM" in warnings[0] or "2" in warnings[0]
    assert mock_vm.available < MIN_AVAILABLE_FOR_DIARIZATION_BYTES


def test_diarization_oom_returns_empty(monkeypatch: pytest.MonkeyPatch) -> None:
    """When Diarizer.diarize raises MemoryError, pipeline returns ([], warnings) (graceful degradation)."""
    import voiceforge.core.pipeline as pipeline_mod

    mock_vm = MagicMock()
    mock_vm.available = 3 * 1024**3  # 3 GB so we don't hit low-memory skip
    monkeypatch.setattr(pipeline_mod, "psutil", MagicMock(virtual_memory=lambda: mock_vm))

    fake_diarizer = MagicMock()
    fake_diarizer.diarize.side_effect = MemoryError("CUDA out of memory")

    def return_fake_diarizer(auth_token: str, restart_hours: int) -> MagicMock:
        return fake_diarizer

    monkeypatch.setattr(pipeline_mod, "_get_cached_diarizer", return_fake_diarizer)

    try:
        import keyring

        monkeypatch.setattr(
            keyring,
            "get_password",
            lambda s, k: "fake-token" if (s == "voiceforge" and k == "huggingface") else None,
        )
    except ImportError:
        pytest.skip("keyring not installed")

    audio_f = np.zeros(16000 * 10, dtype=np.float32)
    segments, warnings = _step2_diarization(audio_f, 16000, pyannote_restart_hours=2)

    assert segments == []
    assert len(warnings) >= 1
