"""W10: Unit tests for daemon, streaming, smart_trigger, model_manager (key scenarios with mocks)."""

from __future__ import annotations

import json
import time
from unittest.mock import MagicMock, patch

import numpy as np
import pytest


def test_daemon_get_settings_returns_json_with_expected_keys(tmp_path, monkeypatch) -> None:
    """Daemon get_settings() returns JSON containing model_size, default_llm, privacy_mode, pii_mode."""
    monkeypatch.setenv("XDG_DATA_HOME", str(tmp_path))
    with patch("voiceforge.core.daemon.Settings") as mock_settings:
        mock_cfg = MagicMock()
        mock_cfg.model_size = "small"
        mock_cfg.default_llm = "anthropic/claude-haiku-4-5"
        mock_cfg.budget_limit_usd = 75.0
        mock_cfg.smart_trigger = False
        mock_cfg.sample_rate = 16000
        mock_cfg.streaming_stt = False
        mock_cfg.pii_mode = "ON"
        mock_settings.return_value = mock_cfg

        from voiceforge.core.daemon import VoiceForgeDaemon

        daemon = VoiceForgeDaemon(iface=None)
        out = daemon.get_settings()
    data = json.loads(out)
    assert data["model_size"] == "small"
    assert data["default_llm"] == "anthropic/claude-haiku-4-5"
    assert data["pii_mode"] == "ON"
    assert data["privacy_mode"] == "ON"


def test_daemon_get_analytics_returns_dict(tmp_path, monkeypatch) -> None:
    """Daemon get_analytics() returns JSON object (from get_stats)."""
    monkeypatch.setenv("XDG_DATA_HOME", str(tmp_path))
    with patch("voiceforge.core.daemon.Settings") as mock_settings:
        mock_settings.return_value = MagicMock()
        with patch("voiceforge.core.metrics.get_stats") as mock_get_stats:
            mock_get_stats.return_value = {"total_cost_usd": 0.5, "by_day": []}

            from voiceforge.core.daemon import VoiceForgeDaemon

            daemon = VoiceForgeDaemon(iface=None)
            out = daemon.get_analytics("7d")
    data = json.loads(out)
    assert "total_cost_usd" in data
    assert data["total_cost_usd"] == pytest.approx(0.5)


def test_smart_trigger_check_returns_false_when_file_missing() -> None:
    """SmartTrigger.check() returns False when ring file does not exist."""
    from voiceforge.audio.smart_trigger import SmartTrigger

    trigger = SmartTrigger(sample_rate=16000)
    assert trigger.check("/nonexistent/ring.pcm") is False


def test_smart_trigger_check_returns_false_when_file_too_small(tmp_path) -> None:
    """SmartTrigger.check() returns False when ring file has insufficient samples."""
    from voiceforge.audio.smart_trigger import SmartTrigger

    ring = tmp_path / "ring.pcm"
    ring.write_bytes(b"\x00\x00" * 1000)
    trigger = SmartTrigger(sample_rate=16000, min_speech_sec=30.0, min_silence_sec=3.0)
    assert trigger.check(str(ring)) is False


def test_model_manager_get_stt_and_llm_ids() -> None:
    """ModelManager returns config model_size and default_llm."""
    from voiceforge.core.model_manager import ModelManager

    cfg = MagicMock()
    cfg.model_size = "tiny"
    cfg.default_llm = "openai/gpt-4o-mini"
    mgr = ModelManager(cfg)
    assert mgr.get_stt_model_size() == "tiny"
    assert mgr.get_llm_model_id() == "openai/gpt-4o-mini"


def test_model_manager_set_get_global() -> None:
    """set_model_manager / get_model_manager roundtrip."""
    from voiceforge.core.model_manager import get_model_manager, set_model_manager

    set_model_manager(None)
    assert get_model_manager() is None
    obj = MagicMock()
    set_model_manager(obj)
    assert get_model_manager() is obj
    set_model_manager(None)


def test_streaming_transcriber_class_exists() -> None:
    """StreamingTranscriber exists and has expected interface."""
    from voiceforge.stt import streaming

    assert hasattr(streaming, "StreamingTranscriber")


def test_streaming_transcriber_passes_language_to_transcribe() -> None:
    """StreamingTranscriber passes language hint to transcriber.transcribe (Roadmap #9/#7)."""
    from voiceforge.stt.streaming import StreamingTranscriber
    from voiceforge.stt.transcriber import Segment

    mock_transcriber = MagicMock()
    mock_transcriber.transcribe.return_value = [
        Segment(start=0.0, end=1.0, text="hello", language="ru", confidence=0.95),
    ]
    chunks: list[tuple[object, object]] = []

    def on_final(seg: object) -> None:
        chunks.append(("final", seg))

    stream = StreamingTranscriber(
        mock_transcriber,
        sample_rate=16000,
        language="ru",
        on_final=on_final,
    )
    audio = np.zeros(200, dtype=np.float32)
    stream.process_chunk(audio, start_offset_sec=0.0)

    mock_transcriber.transcribe.assert_called_once()
    call_kw = mock_transcriber.transcribe.call_args[1]
    assert call_kw.get("language") == "ru"
    assert len(chunks) == 1
    assert chunks[0][0] == "final"


# --- Daemon: more coverage for get_streaming_transcript, get_api_version, get_capabilities, get_sessions/get_session_detail/get_indexed_paths (exception/no file) ---


def test_daemon_get_streaming_transcript_returns_json(tmp_path, monkeypatch) -> None:
    """Daemon get_streaming_transcript() returns JSON with partial and finals."""
    monkeypatch.setenv("XDG_DATA_HOME", str(tmp_path))
    with patch("voiceforge.core.daemon.Settings") as mock_settings:
        mock_settings.return_value = MagicMock()
        from voiceforge.core.daemon import VoiceForgeDaemon

        daemon = VoiceForgeDaemon(iface=None)
        out = daemon.get_streaming_transcript()
    data = json.loads(out)
    assert "partial" in data
    assert "finals" in data
    assert data["partial"] == ""
    assert data["finals"] == []


def test_daemon_get_api_version_and_capabilities(tmp_path, monkeypatch) -> None:
    """Daemon get_api_version() and get_capabilities() return expected strings."""
    monkeypatch.setenv("XDG_DATA_HOME", str(tmp_path))
    with patch("voiceforge.core.daemon.Settings") as mock_settings:
        mock_settings.return_value = MagicMock()
        from voiceforge.core.daemon import VoiceForgeDaemon

        daemon = VoiceForgeDaemon(iface=None)
    assert daemon.get_api_version() == "1.0"
    caps = json.loads(daemon.get_capabilities())
    assert caps["api_version"] == "1.0"
    assert "listen" in caps["features"]
    assert caps["features"]["listen"] is True
    assert caps["features"].get("envelope_v1") is True


def test_daemon_analyze_timeout_returns_error(tmp_path, monkeypatch) -> None:
    """Daemon analyze() returns ANALYZE_TIMEOUT JSON when pipeline exceeds analyze_timeout_sec (#39)."""
    monkeypatch.setenv("XDG_DATA_HOME", str(tmp_path))

    def block_pipeline(*args: object, **kwargs: object) -> tuple[str, list, object]:
        time.sleep(10)
        return ("", [], None)

    with patch("voiceforge.core.daemon.Settings") as mock_settings:
        mock_cfg = MagicMock()
        mock_cfg.analyze_timeout_sec = 0.05
        mock_settings.return_value = mock_cfg
        with patch("voiceforge.main.run_analyze_pipeline", side_effect=block_pipeline):
            from voiceforge.core.daemon import VoiceForgeDaemon

            daemon = VoiceForgeDaemon(iface=None)
            result = daemon.analyze(30)
    data = json.loads(result)
    assert "error" in data
    assert data["error"]["code"] == "ANALYZE_TIMEOUT"
    assert data["error"].get("retryable") is True


def test_daemon_get_sessions_returns_empty_on_exception(tmp_path, monkeypatch) -> None:
    """Daemon get_sessions() returns [] when TranscriptLog fails."""
    monkeypatch.setenv("XDG_DATA_HOME", str(tmp_path))
    with patch("voiceforge.core.daemon.Settings") as mock_settings:
        mock_settings.return_value = MagicMock()
        with patch("voiceforge.core.transcript_log.TranscriptLog", side_effect=RuntimeError("no db")):
            from voiceforge.core.daemon import VoiceForgeDaemon

            daemon = VoiceForgeDaemon(iface=None)
            out = daemon.get_sessions(10)
    assert out == "[]"


def test_daemon_get_session_detail_returns_empty_obj_on_exception(tmp_path, monkeypatch) -> None:
    """Daemon get_session_detail() returns {} when TranscriptLog fails."""
    monkeypatch.setenv("XDG_DATA_HOME", str(tmp_path))
    with patch("voiceforge.core.daemon.Settings") as mock_settings:
        mock_settings.return_value = MagicMock()
        with patch("voiceforge.core.transcript_log.TranscriptLog", side_effect=RuntimeError("no db")):
            from voiceforge.core.daemon import VoiceForgeDaemon

            daemon = VoiceForgeDaemon(iface=None)
            out = daemon.get_session_detail(1)
    assert out == "{}"


def test_daemon_get_indexed_paths_returns_empty_when_no_db(tmp_path, monkeypatch) -> None:
    """Daemon get_indexed_paths() returns [] when RAG DB file does not exist."""
    monkeypatch.setenv("XDG_DATA_HOME", str(tmp_path))
    with patch("voiceforge.core.daemon.Settings") as mock_settings:
        mock_cfg = MagicMock()
        mock_cfg.get_rag_db_path.return_value = str(tmp_path / "nonexistent_rag.db")
        mock_settings.return_value = mock_cfg
        from voiceforge.core.daemon import VoiceForgeDaemon

        daemon = VoiceForgeDaemon(iface=None)
        out = daemon.get_indexed_paths()
    assert out == "[]"


def test_daemon_get_analytics_returns_empty_obj_on_exception(tmp_path, monkeypatch) -> None:
    """Daemon get_analytics() returns {} when get_stats fails."""
    monkeypatch.setenv("XDG_DATA_HOME", str(tmp_path))
    with patch("voiceforge.core.daemon.Settings") as mock_settings:
        mock_settings.return_value = MagicMock()
        with patch("voiceforge.core.metrics.get_stats", side_effect=RuntimeError("no metrics")):
            from voiceforge.core.daemon import VoiceForgeDaemon

            daemon = VoiceForgeDaemon(iface=None)
            out = daemon.get_analytics("7d")
    assert out == "{}"


def test_daemon_get_analytics_parses_7d_and_30d(tmp_path, monkeypatch) -> None:
    """Daemon get_analytics() parses last='7d' and '30' into days and returns get_stats JSON."""
    monkeypatch.setenv("XDG_DATA_HOME", str(tmp_path))
    with patch("voiceforge.core.daemon.Settings") as mock_settings:
        mock_settings.return_value = MagicMock()
        with patch("voiceforge.core.metrics.get_stats") as mock_get_stats:
            mock_get_stats.return_value = {"total_cost_usd": 1.0, "by_day": []}
            from voiceforge.core.daemon import VoiceForgeDaemon

            daemon = VoiceForgeDaemon(iface=None)
            out7 = daemon.get_analytics("7d")
            out30 = daemon.get_analytics("30")
    assert json.loads(out7)["total_cost_usd"] == 1.0
    assert json.loads(out30)["total_cost_usd"] == 1.0
    assert mock_get_stats.call_count == 2
    calls = [c[1] for c in mock_get_stats.call_args_list]
    assert calls[0]["days"] == 7
    assert calls[1]["days"] == 30


# --- SmartTrigger: VAD no segments, cooldown, and fired path (mocked) ---


def test_smart_trigger_check_returns_false_when_vad_returns_no_segments(tmp_path) -> None:
    """SmartTrigger.check() returns False when VAD returns no speech segments."""
    from voiceforge.audio.smart_trigger import SmartTrigger

    # File large enough for min_speech + min_silence
    min_samples = int(16000 * (30.0 + 3.0)) * 2
    ring = tmp_path / "ring.pcm"
    ring.write_bytes(b"\x00\x00" * min_samples)
    with patch("faster_whisper.vad.get_speech_timestamps", return_value=[]):
        trigger = SmartTrigger(sample_rate=16000)
        assert trigger.check(str(ring)) is False


def test_smart_trigger_check_returns_false_when_speech_too_short(tmp_path) -> None:
    """SmartTrigger.check() returns False when total speech duration < min_speech_sec."""
    from voiceforge.audio.smart_trigger import SmartTrigger

    min_samples = int(16000 * (30.0 + 3.0)) * 2
    ring = tmp_path / "ring.pcm"
    ring.write_bytes(b"\x00\x00" * min_samples)
    # Segments that sum to 10s speech (less than 30s)
    with patch(
        "faster_whisper.vad.get_speech_timestamps",
        return_value=[{"start": 0, "end": 160000}],
    ):
        trigger = SmartTrigger(sample_rate=16000, min_speech_sec=30.0)
        assert trigger.check(str(ring)) is False


def test_smart_trigger_check_returns_true_when_conditions_met(tmp_path) -> None:
    """SmartTrigger.check() returns True when enough speech, silence, and past cooldown."""
    from voiceforge.audio.smart_trigger import SmartTrigger

    # 35s of "audio" (33s speech + 2s trailing would fail silence; we need 33s speech + 4s silence)
    n_samples = 16000 * 37
    ring = tmp_path / "ring.pcm"
    ring.write_bytes(b"\x00\x00" * n_samples)
    # Speech 0..33s, then silence 33..37s (4s)
    with patch(
        "faster_whisper.vad.get_speech_timestamps",
        return_value=[{"start": 0, "end": 33 * 16000}],
    ):
        trigger = SmartTrigger(sample_rate=16000, min_speech_sec=30.0, min_silence_sec=3.0, cooldown_sec=0.0)
        assert trigger.check(str(ring)) is True


# --- Streaming: process_chunk empty, feed + flush (mocked) ---


def test_streaming_process_chunk_empty_array_no_call(tmp_path) -> None:
    """StreamingTranscriber.process_chunk() with empty array does not call transcriber."""
    from voiceforge.stt.streaming import StreamingTranscriber

    mock_transcriber = MagicMock()
    stream = StreamingTranscriber(mock_transcriber, sample_rate=16000)
    stream.process_chunk(np.array([], dtype=np.float32), start_offset_sec=0.0)
    mock_transcriber.transcribe.assert_not_called()


def test_streaming_feed_flushes_when_buffer_full() -> None:
    """StreamingTranscriber.feed() flushes chunk when buffer duration >= chunk_duration."""
    from voiceforge.stt.streaming import StreamingTranscriber
    from voiceforge.stt.transcriber import Segment

    mock_transcriber = MagicMock()
    mock_transcriber.transcribe.return_value = [
        Segment(start=0.0, end=1.0, text="hi", language="en", confidence=0.9),
    ]
    finals: list[object] = []

    def on_final(seg: object) -> None:
        finals.append(seg)

    stream = StreamingTranscriber(
        mock_transcriber,
        sample_rate=16000,
        chunk_duration_sec=2.0,
        overlap_sec=0.5,
        on_final=on_final,
    )
    # Feed 2.5s of audio so one chunk is flushed
    n_samples = int(16000 * 2.5)
    stream.feed(np.zeros(n_samples, dtype=np.float32))
    assert mock_transcriber.transcribe.called
    assert len(finals) >= 1


# --- model_manager: swap_model (stt/llm/unknown), unload_stt, get_transcriber (mocked) ---


def test_model_manager_swap_model_stt_returns_ok() -> None:
    """ModelManager.swap_model('stt', 'tiny') returns 'ok'."""
    from voiceforge.core.model_manager import ModelManager

    mgr = ModelManager(MagicMock())
    out = mgr.swap_model("stt", "tiny")
    assert out == "ok"
    assert mgr.get_stt_model_size() == "tiny"


def test_model_manager_swap_model_llm_returns_ok() -> None:
    """ModelManager.swap_model('llm', 'openai/gpt-4o') returns 'ok'."""
    from voiceforge.core.model_manager import ModelManager

    mgr = ModelManager(MagicMock())
    out = mgr.swap_model("llm", "openai/gpt-4o")
    assert out == "ok"
    assert mgr.get_llm_model_id() == "openai/gpt-4o"


def test_model_manager_swap_model_unknown_type_returns_error() -> None:
    """ModelManager.swap_model('unknown', 'x') returns error string."""
    from voiceforge.core.model_manager import ModelManager

    mgr = ModelManager(MagicMock())
    out = mgr.swap_model("unknown", "x")
    assert out.startswith("error:")
    assert "unknown model_type" in out


def test_model_manager_swap_model_empty_name_returns_error() -> None:
    """ModelManager.swap_model('stt', '') returns error."""
    from voiceforge.core.model_manager import ModelManager

    mgr = ModelManager(MagicMock())
    out = mgr.swap_model("stt", "")
    assert "error" in out


def test_model_manager_unload_stt_clears_transcriber() -> None:
    """ModelManager.unload_stt() clears _transcriber and runs gc."""
    from voiceforge.core.model_manager import ModelManager

    cfg = MagicMock()
    cfg.model_size = "tiny"
    cfg.default_llm = "x"
    mgr = ModelManager(cfg)
    mgr._transcriber = MagicMock()
    mgr.unload_stt()
    assert mgr._transcriber is None


def test_model_manager_unload_stt_calls_torch_cuda_when_available() -> None:
    """ModelManager.unload_stt() calls torch.cuda.empty_cache() when cuda is available."""
    from voiceforge.core.model_manager import ModelManager

    mock_torch = MagicMock()
    mock_torch.cuda.is_available.return_value = True
    mock_torch.cuda.empty_cache = MagicMock()
    cfg = MagicMock()
    cfg.model_size = "tiny"
    cfg.default_llm = "x"
    mgr = ModelManager(cfg)
    mgr._transcriber = MagicMock()
    with patch.dict("sys.modules", {"torch": mock_torch}):
        mgr.unload_stt()
    mock_torch.cuda.empty_cache.assert_called_once()
    assert mgr._transcriber is None


def test_model_manager_get_transcriber_lazy_loads_and_reuses() -> None:
    """ModelManager.get_transcriber() lazy-loads Transcriber and reuses for same size."""
    from voiceforge.core.model_manager import ModelManager

    cfg = MagicMock()
    cfg.model_size = "tiny"
    cfg.default_llm = "x"
    mgr = ModelManager(cfg)
    with patch("voiceforge.stt.transcriber.Transcriber") as MockTranscriber:
        mock_t = MagicMock(spec=["_model_size"])
        mock_t._model_size = "tiny"
        MockTranscriber.return_value = mock_t
        t1 = mgr.get_transcriber()
        t2 = mgr.get_transcriber()
        assert t1 is t2
        MockTranscriber.assert_called_once()


# --- streaming: resample (same rate; different rate with scipy), process_chunk int16, on_partial ---


def test_streaming_resample_same_rate_passthrough() -> None:
    """When from_rate == 16000, _resample_float_to_16k returns input and 16000."""
    from voiceforge.stt.streaming import _resample_float_to_16k

    audio = np.zeros(1600, dtype=np.float32)
    out, rate = _resample_float_to_16k(audio, 16000)
    assert rate == 16000
    assert out is audio


def test_streaming_resample_different_rate_uses_scipy() -> None:
    """When from_rate != 16000 and scipy available, resamples to 16k."""
    from voiceforge.stt.streaming import _resample_float_to_16k

    # 44100 Hz, 0.1s -> 4410 samples -> 16k * 0.1 = 1600 samples
    audio = np.zeros(4410, dtype=np.float32)
    out, rate = _resample_float_to_16k(audio, 44100)
    assert rate == 16000
    assert len(out) == 1600
    assert out.dtype == np.float32


def test_streaming_resample_n_less_than_one_returns_unchanged() -> None:
    """When computed n < 1 (tiny audio), returns (audio_f, from_rate)."""
    from voiceforge.stt.streaming import _resample_float_to_16k

    audio = np.zeros(10, dtype=np.float32)
    out, rate = _resample_float_to_16k(audio, 200000)
    assert rate == 200000
    assert out is audio


def test_streaming_process_chunk_int16_converts_to_float() -> None:
    """StreamingTranscriber.process_chunk() accepts int16 and calls transcribe."""
    from voiceforge.stt.streaming import StreamingTranscriber
    from voiceforge.stt.transcriber import Segment

    mock_transcriber = MagicMock()
    mock_transcriber.transcribe.return_value = [
        Segment(start=0.0, end=0.5, text="x", language="en", confidence=0.9),
    ]
    stream = StreamingTranscriber(mock_transcriber, sample_rate=16000)
    # > 100 samples so _process_chunk runs
    stream.process_chunk(np.zeros(200, dtype=np.int16), start_offset_sec=0.0)
    mock_transcriber.transcribe.assert_called_once()


def test_streaming_on_partial_called() -> None:
    """StreamingTranscriber calls on_partial when segment has text."""
    from voiceforge.stt.streaming import StreamingTranscriber
    from voiceforge.stt.transcriber import Segment

    mock_transcriber = MagicMock()
    mock_transcriber.transcribe.return_value = [
        Segment(start=0.0, end=1.0, text="hello", language="en", confidence=0.95),
    ]
    partials: list[str] = []

    def on_partial(text: str) -> None:
        partials.append(text)

    stream = StreamingTranscriber(
        mock_transcriber,
        sample_rate=16000,
        on_partial=on_partial,
    )
    stream.process_chunk(np.zeros(500, dtype=np.float32), start_offset_sec=0.0)
    assert partials == ["hello"]


def test_streaming_process_chunk_skips_too_short_audio() -> None:
    """StreamingTranscriber.process_chunk() with < 100 samples does not call transcribe."""
    from voiceforge.stt.streaming import StreamingTranscriber

    mock_transcriber = MagicMock()
    stream = StreamingTranscriber(mock_transcriber, sample_rate=16000)
    stream.process_chunk(np.zeros(50, dtype=np.float32), start_offset_sec=0.0)
    mock_transcriber.transcribe.assert_not_called()


# --- daemon: _streaming_language_hint, _env_flag, _pid_path, status, swap_model, is_listening ---


def test_daemon_streaming_language_hint_auto_returns_none() -> None:
    """_streaming_language_hint returns None for 'auto' and ''."""
    from voiceforge.core.daemon import _streaming_language_hint

    cfg = MagicMock()
    cfg.language = "auto"
    assert _streaming_language_hint(cfg) is None
    cfg.language = ""
    assert _streaming_language_hint(cfg) is None


def test_daemon_streaming_language_hint_explicit_returns_lang() -> None:
    """_streaming_language_hint returns language when set (e.g. 'ru')."""
    from voiceforge.core.daemon import _streaming_language_hint

    cfg = MagicMock()
    cfg.language = "ru"
    assert _streaming_language_hint(cfg) == "ru"


def test_daemon_env_flag_default_and_true() -> None:
    """_env_flag returns default when unset; True for 1/true/yes/on."""
    from voiceforge.core.daemon import _env_flag

    assert _env_flag("VOICEFORGE_NONEXISTENT_XYZ", default=False) is False
    assert _env_flag("VOICEFORGE_NONEXISTENT_XYZ", default=True) is True


def test_daemon_env_flag_false_for_zero() -> None:
    """_env_flag returns False for 0/false/no/off."""
    from voiceforge.core.daemon import _env_flag

    with patch.dict("os.environ", {"VOICEFORGE_IPC_ENVELOPE": "0"}, clear=False):
        assert _env_flag("VOICEFORGE_IPC_ENVELOPE", default=True) is False
    with patch.dict("os.environ", {"VOICEFORGE_IPC_ENVELOPE": "false"}, clear=False):
        assert _env_flag("VOICEFORGE_IPC_ENVELOPE", default=True) is False


def test_daemon_pid_path_uses_xdg_or_cache() -> None:
    """_pid_path() uses XDG_RUNTIME_DIR or ~/.cache."""
    from voiceforge.core.daemon import PID_FILE_NAME, _pid_path

    with patch.dict("os.environ", {"XDG_RUNTIME_DIR": "/run/user/1000"}, clear=False):
        p = _pid_path()
        assert str(p) == "/run/user/1000/voiceforge.pid"
    with patch.dict("os.environ", {}, clear=True):
        p = _pid_path()
        assert p.name == PID_FILE_NAME
        assert ".cache" in str(p)


def test_daemon_status_calls_get_status_text(tmp_path, monkeypatch) -> None:
    """Daemon status() returns get_status_text() result."""
    monkeypatch.setenv("XDG_DATA_HOME", str(tmp_path))
    with patch("voiceforge.core.daemon.Settings") as mock_settings:
        mock_settings.return_value = MagicMock()
        with patch("voiceforge.main.get_status_text", return_value="RAM: 100 MB"):
            from voiceforge.core.daemon import VoiceForgeDaemon

            daemon = VoiceForgeDaemon(iface=None)
            assert daemon.status() == "RAM: 100 MB"


def test_daemon_swap_model_delegates_to_model_manager(tmp_path, monkeypatch) -> None:
    """Daemon swap_model() delegates to ModelManager.swap_model."""
    monkeypatch.setenv("XDG_DATA_HOME", str(tmp_path))
    with patch("voiceforge.core.daemon.Settings") as mock_settings:
        mock_settings.return_value = MagicMock()
        from voiceforge.core.daemon import VoiceForgeDaemon

        daemon = VoiceForgeDaemon(iface=None)
        out = daemon.swap_model("llm", "openai/gpt-4o")
        assert out == "ok"


def test_daemon_is_listening_initially_false(tmp_path, monkeypatch) -> None:
    """Daemon is_listening() is False before listen_start."""
    monkeypatch.setenv("XDG_DATA_HOME", str(tmp_path))
    with patch("voiceforge.core.daemon.Settings") as mock_settings:
        mock_settings.return_value = MagicMock()
        from voiceforge.core.daemon import VoiceForgeDaemon

        daemon = VoiceForgeDaemon(iface=None)
        assert daemon.is_listening() is False


def test_daemon_listen_start_idempotent(tmp_path, monkeypatch) -> None:
    """Daemon listen_start() when already active returns without starting a second thread."""
    monkeypatch.setenv("XDG_DATA_HOME", str(tmp_path))
    with patch("voiceforge.core.daemon.Settings") as mock_settings:
        mock_settings.return_value = MagicMock()
        from voiceforge.core.daemon import VoiceForgeDaemon

        daemon = VoiceForgeDaemon(iface=None)
        daemon._listen_active = True
        daemon.listen_start()
        daemon.listen_start()
        assert daemon.is_listening() is True


def test_daemon_listen_stop_when_not_active_no_op(tmp_path, monkeypatch) -> None:
    """Daemon listen_stop() when not listening returns without error."""
    monkeypatch.setenv("XDG_DATA_HOME", str(tmp_path))
    with patch("voiceforge.core.daemon.Settings") as mock_settings:
        mock_settings.return_value = MagicMock()
        from voiceforge.core.daemon import VoiceForgeDaemon

        daemon = VoiceForgeDaemon(iface=None)
        daemon.listen_stop()
        assert daemon.is_listening() is False


def test_daemon_get_sessions_success_returns_json(tmp_path, monkeypatch) -> None:
    """Daemon get_sessions() returns JSON array when TranscriptLog works."""
    monkeypatch.setenv("XDG_DATA_HOME", str(tmp_path))

    class FakeSession:
        id = 1
        started_at = "2025-01-01T00:00:00"
        ended_at = "2025-01-01T00:05:00"
        duration_sec = 300
        segments_count = 10

    with patch("voiceforge.core.daemon.Settings") as mock_settings:
        mock_settings.return_value = MagicMock()
        with patch("voiceforge.core.transcript_log.TranscriptLog") as MockLog:
            mock_db = MagicMock()
            mock_db.get_sessions.return_value = [FakeSession()]
            mock_db.__enter__ = lambda self: self
            mock_db.__exit__ = lambda *a: None
            MockLog.return_value = mock_db
            from voiceforge.core.daemon import VoiceForgeDaemon

            daemon = VoiceForgeDaemon(iface=None)
            out = daemon.get_sessions(5)
    data = json.loads(out)
    assert len(data) == 1
    assert data[0]["id"] == 1
    assert data[0]["segments_count"] == 10


def test_daemon_get_indexed_paths_returns_paths_when_db_exists(tmp_path, monkeypatch) -> None:
    """Daemon get_indexed_paths() returns JSON array when RAG DB exists and has rows."""
    monkeypatch.setenv("XDG_DATA_HOME", str(tmp_path))
    rag_db = tmp_path / "rag.db"
    rag_db.write_bytes(b"")  # empty sqlite
    import sqlite3

    conn = sqlite3.connect(str(rag_db))
    conn.execute("CREATE TABLE chunks (source TEXT)")
    conn.execute("INSERT INTO chunks (source) VALUES (?), (?)", ("/a/doc.pdf", "/b/file.txt"))
    conn.commit()
    conn.close()

    with patch("voiceforge.core.daemon.Settings") as mock_settings:
        mock_cfg = MagicMock()
        mock_cfg.get_rag_db_path.return_value = str(rag_db)
        mock_settings.return_value = mock_cfg
        from voiceforge.core.daemon import VoiceForgeDaemon

        daemon = VoiceForgeDaemon(iface=None)
        out = daemon.get_indexed_paths()
    data = json.loads(out)
    assert data == ["/a/doc.pdf", "/b/file.txt"]


def test_smart_trigger_check_returns_false_when_silence_too_short(tmp_path) -> None:
    """SmartTrigger.check() returns False when silence after speech < min_silence_sec."""
    from voiceforge.audio.smart_trigger import SmartTrigger

    # 37s total; speech 0..35s -> 2s silence (need 3s)
    n_samples = 16000 * 37
    ring = tmp_path / "ring.pcm"
    ring.write_bytes(b"\x00\x00" * n_samples)
    with patch(
        "faster_whisper.vad.get_speech_timestamps",
        return_value=[{"start": 0, "end": 35 * 16000}],
    ):
        trigger = SmartTrigger(sample_rate=16000, min_speech_sec=30.0, min_silence_sec=3.0, cooldown_sec=0.0)
        assert trigger.check(str(ring)) is False
