"""W5: Pipeline integration tests — run AnalysisPipeline with mocks (no real STT/RAG)."""

from __future__ import annotations

from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

import numpy as np
import pytest

from voiceforge.core.pipeline import (
    AnalysisPipeline,
    PipelineResult,
    TARGET_SAMPLE_RATE,
    _prepare_audio,
    _resample_to_16k,
)


def _make_cfg(tmp_path: Path, ring_path: Path, rag_path: Path | None = None) -> SimpleNamespace:
    cfg = SimpleNamespace(
        sample_rate=TARGET_SAMPLE_RATE,
        model_size="tiny",
        pyannote_restart_hours=2,
        pipeline_step2_timeout_sec=10.0,
        pii_mode="ON",
        calendar_context_enabled=False,
        language="auto",
    )
    cfg.get_ring_file_path = lambda: str(ring_path)
    cfg.get_rag_db_path = lambda: str(rag_path or (tmp_path / "rag.db"))
    return cfg


def test_prepare_audio_missing_ring_returns_error(tmp_path: Path) -> None:
    """When ring file does not exist, _prepare_audio returns (None, error_str)."""
    ring = tmp_path / "ring.raw"
    cfg = _make_cfg(tmp_path, ring)
    result = _prepare_audio(cfg, seconds=1)
    assert result[0] is None
    assert isinstance(result[1], str)
    assert len(result[1]) > 0


def test_prepare_audio_insufficient_audio_returns_error(tmp_path: Path) -> None:
    """When ring has less than 1 second of samples, _prepare_audio returns (None, error_str)."""
    ring = tmp_path / "ring.raw"
    ring.write_bytes(b"\x00\x00" * 100)
    cfg = _make_cfg(tmp_path, ring)
    result = _prepare_audio(cfg, seconds=1)
    assert result[0] is None
    assert isinstance(result[1], str)


def test_prepare_audio_returns_audio_and_rate(tmp_path: Path) -> None:
    """With enough PCM int16 data, _prepare_audio returns (audio, rate)."""
    # 2 seconds at 16 kHz = 32000 samples = 64000 bytes
    num_samples = TARGET_SAMPLE_RATE * 2
    ring = tmp_path / "ring.raw"
    ring.write_bytes(np.zeros(num_samples, dtype=np.int16).tobytes())
    cfg = _make_cfg(tmp_path, ring)
    result = _prepare_audio(cfg, seconds=2)
    assert result[0] is not None
    audio, rate = result[0], result[1]
    assert isinstance(audio, np.ndarray)
    assert audio.dtype == np.int16
    assert rate == TARGET_SAMPLE_RATE
    assert len(audio) >= TARGET_SAMPLE_RATE


def test_resample_to_16k_passthrough() -> None:
    """When from_rate == 16k, _resample_to_16k returns array unchanged."""
    arr = np.zeros(1600, dtype=np.int16)
    out = _resample_to_16k(arr, 16000)
    np.testing.assert_array_equal(out, arr)


def test_pipeline_run_returns_none_when_no_ring(tmp_path: Path) -> None:
    """AnalysisPipeline.run() returns (None, error_str) when ring file missing."""
    ring = tmp_path / "ring.raw"
    cfg = _make_cfg(tmp_path, ring)
    with AnalysisPipeline(cfg) as pipeline:
        result, err = pipeline.run(seconds=1)
    assert result is None
    assert err is not None


@patch("voiceforge.core.pipeline._step1_stt")
def test_pipeline_run_returns_result_with_mocked_stt(
    mock_stt: object,
    tmp_path: Path,
) -> None:
    """With mocked STT, pipeline runs step2 and returns PipelineResult."""
    num_samples = TARGET_SAMPLE_RATE * 2
    ring = tmp_path / "ring.raw"
    ring.write_bytes(np.zeros(num_samples, dtype=np.int16).tobytes())
    cfg = _make_cfg(tmp_path, ring)

    class FakeSegment:
        def __init__(self, text: str = "hello") -> None:
            self.text = text
            self.start = 0.0
            self.end = 1.0

    def fake_step1(
        audio: np.ndarray,
        sample_rate: int,
        model_size: str,
        language_hint: str | None = None,
    ) -> tuple[list, str]:
        return ([FakeSegment("mocked")], "mocked transcript")

    mock_stt.side_effect = fake_step1

    with AnalysisPipeline(cfg) as pipeline:
        result, err = pipeline.run(seconds=2)

    assert err is None
    assert result is not None
    assert isinstance(result, PipelineResult)
    assert result.transcript == "mocked transcript"
    assert len(result.segments) == 1
    assert result.segments[0].text == "mocked"
    # Step2 (diarization, RAG, PII) run; without real services we get empty/transcript
    assert result.diar_segments is not None
    assert result.context is not None
    assert result.transcript_redacted is not None
