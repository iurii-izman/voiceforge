"""W5: Pipeline integration tests — run AnalysisPipeline with mocks (no real STT/RAG)."""

from __future__ import annotations

from pathlib import Path
from types import SimpleNamespace
from unittest.mock import MagicMock, patch

import numpy as np
import pytest

from voiceforge.core.pipeline import (
    AnalysisPipeline,
    PipelineResult,
    TARGET_SAMPLE_RATE,
    _get_language_hint,
    _prepare_audio,
    _rag_merge_results,
    _resample_to_16k,
    _with_calendar_context,
)
from voiceforge.rag.searcher import SearchResult


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


def test_prepare_audio_resamples_when_rate_not_16k(tmp_path: Path) -> None:
    """When cfg.sample_rate is 48000, _prepare_audio resamples to 16k and returns 16k rate."""
    # 2 seconds at 48 kHz = 96000 samples
    rate_48k = 48000
    num_samples = rate_48k * 2
    ring = tmp_path / "ring.raw"
    ring.write_bytes(np.zeros(num_samples, dtype=np.int16).tobytes())
    cfg = _make_cfg(tmp_path, ring)
    cfg.sample_rate = rate_48k
    result = _prepare_audio(cfg, seconds=2)
    assert result[0] is not None
    audio, rate = result[0], result[1]
    assert rate == TARGET_SAMPLE_RATE
    assert len(audio) == TARGET_SAMPLE_RATE * 2


def test_resample_to_16k_passthrough() -> None:
    """When from_rate == 16k, _resample_to_16k returns array unchanged."""
    arr = np.zeros(1600, dtype=np.int16)
    out = _resample_to_16k(arr, 16000)
    np.testing.assert_array_equal(out, arr)


def test_resample_to_16k_resamples_when_scipy_available() -> None:
    """When from_rate != 16k and scipy available, _resample_to_16k resamples."""
    arr = np.zeros(48000, dtype=np.int16)  # 1 s at 48 kHz
    out = _resample_to_16k(arr, 48000)
    assert out is not None
    assert out.dtype == np.int16
    assert len(out) == 16000


def test_get_language_hint_auto_returns_none() -> None:
    """_get_language_hint returns None for language 'auto' or missing."""
    cfg = SimpleNamespace(language="auto")
    assert _get_language_hint(cfg) is None
    cfg2 = SimpleNamespace()
    assert _get_language_hint(cfg2) is None


def test_get_language_hint_explicit_returns_value() -> None:
    """_get_language_hint returns language when set (e.g. 'en')."""
    cfg = SimpleNamespace(language="en")
    assert _get_language_hint(cfg) == "en"


def test_with_calendar_context_disabled_returns_unchanged() -> None:
    """_with_calendar_context returns context unchanged when disabled."""
    cfg = SimpleNamespace(calendar_context_enabled=False)
    assert _with_calendar_context("existing", cfg) == "existing"


def test_with_calendar_context_enabled_injects_calendar(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """_with_calendar_context appends calendar context when enabled and available."""
    monkeypatch.setattr(
        "voiceforge.calendar.caldav_poll.get_next_meeting_context",
        lambda **kw: ("Next meeting: Standup — 2025-03-04T10:00:00+00:00", None),
    )
    cfg = SimpleNamespace(calendar_context_enabled=True)
    out = _with_calendar_context("rag context", cfg)
    assert "rag context" in out
    assert "Calendar" in out
    assert "Standup" in out


def test_with_calendar_context_exception_returns_context_unchanged(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """_with_calendar_context on exception returns context without calendar."""
    monkeypatch.setattr(
        "voiceforge.calendar.caldav_poll.get_next_meeting_context",
        lambda **kw: (_ for _ in ()).throw(RuntimeError("cal error")),
    )
    cfg = SimpleNamespace(calendar_context_enabled=True)
    out = _with_calendar_context("rag context", cfg)
    assert out == "rag context"


def test_with_calendar_context_enabled_empty_cal_returns_unchanged(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """_with_calendar_context when calendar returns empty string leaves context unchanged."""
    monkeypatch.setattr(
        "voiceforge.calendar.caldav_poll.get_next_meeting_context",
        lambda **kw: ("", None),
    )
    cfg = SimpleNamespace(calendar_context_enabled=True)
    out = _with_calendar_context("rag context", cfg)
    assert out == "rag context"


def test_rag_merge_results_empty_queries_returns_empty() -> None:
    """_rag_merge_results with no queries returns empty string."""
    searcher = MagicMock()
    assert _rag_merge_results([], searcher) == ""
    assert _rag_merge_results(["  ", ""], searcher) == ""


def test_rag_merge_results_merges_by_chunk_id() -> None:
    """_rag_merge_results merges results by chunk_id keeping higher score."""
    r1 = SearchResult(chunk_id=1, content="first", source="", page=0, chunk_index=0, timestamp="", score=0.8)
    r2 = SearchResult(chunk_id=1, content="first", source="", page=0, chunk_index=0, timestamp="", score=0.9)
    r3 = SearchResult(chunk_id=2, content="second", source="", page=0, chunk_index=0, timestamp="", score=0.7)
    searcher = MagicMock()
    searcher.search = MagicMock(side_effect=[[r1, r3], [r2]])
    out = _rag_merge_results(["q1", "q2"], searcher)
    assert "first" in out
    assert "second" in out
    searcher.search.assert_called()


def test_resample_to_16k_no_scipy_returns_unchanged(monkeypatch: pytest.MonkeyPatch) -> None:
    """When scipy is not available, _resample_to_16k returns audio unchanged."""
    import builtins

    orig_import = builtins.__import__

    def no_scipy(name: str, *args: object, **kwargs: object):  # type: ignore[no-untyped-def]
        if name == "scipy.signal":
            raise ImportError("No module named 'scipy'")
        return orig_import(name, *args, **kwargs)

    with patch.object(builtins, "__import__", side_effect=no_scipy):
        arr = np.zeros(48000, dtype=np.int16)
        out = _resample_to_16k(arr, 48000)
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
def test_pipeline_run_returns_none_when_stt_raises(
    mock_stt: object,
    tmp_path: Path,
) -> None:
    """When _step1_stt raises, pipeline.run returns (None, error_str)."""
    num_samples = TARGET_SAMPLE_RATE * 2
    ring = tmp_path / "ring.raw"
    ring.write_bytes(np.zeros(num_samples, dtype=np.int16).tobytes())
    cfg = _make_cfg(tmp_path, ring)
    mock_stt.side_effect = RuntimeError("STT failed")
    with AnalysisPipeline(cfg) as pipeline:
        result, err = pipeline.run(seconds=2)
    assert result is None
    assert err is not None


@patch("voiceforge.core.pipeline._step1_stt")
def test_pipeline_run_returns_none_when_stt_import_error(
    mock_stt: object,
    tmp_path: Path,
) -> None:
    """When _step1_stt raises ImportError, pipeline.run returns (None, install_deps message)."""
    num_samples = TARGET_SAMPLE_RATE * 2
    ring = tmp_path / "ring.raw"
    ring.write_bytes(np.zeros(num_samples, dtype=np.int16).tobytes())
    cfg = _make_cfg(tmp_path, ring)
    mock_stt.side_effect = ImportError("faster_whisper")
    with AnalysisPipeline(cfg) as pipeline:
        result, err = pipeline.run(seconds=2)
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
