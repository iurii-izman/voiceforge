"""Audio/STT lifecycle and cheap perf-confidence batch (#118)."""

from __future__ import annotations

import json
import sys
import types
from types import SimpleNamespace

import numpy as np
from typer.testing import CliRunner

import voiceforge.main as main_mod
from voiceforge.stt.streaming import StreamingTranscriber
from voiceforge.stt.transcriber import Segment, Transcriber

runner = CliRunner()


class _FakeAudioCapture:
    def __init__(self, sample_rate: int, buffer_seconds: float, monitor_source: str | None) -> None:
        self.sample_rate = sample_rate
        self.buffer_seconds = buffer_seconds
        self.monitor_source = monitor_source

    def start(self) -> None:
        return None

    def stop(self) -> None:
        return None

    def get_chunk(self, seconds: float) -> tuple[np.ndarray, np.ndarray]:
        data = np.zeros(int(max(16, seconds)), dtype=np.int16)
        return data, data


def _last_json_line(stdout: str) -> dict:
    for line in reversed([line.strip() for line in stdout.splitlines() if line.strip()]):
        if line.startswith("{") and line.endswith("}"):
            return json.loads(line)
    raise AssertionError(f"No JSON payload found in output: {stdout}")


def test_streaming_process_chunk_reuses_float32_buffer_without_resample() -> None:
    seen: list[np.ndarray] = []

    class FakeTranscriber:
        def transcribe(self, audio, **kwargs):  # type: ignore[no-untyped-def]
            seen.append(audio)
            return [Segment(start=0.0, end=0.5, text="ok", language="en", confidence=0.9)]

    audio = np.linspace(-0.25, 0.25, 512, dtype=np.float32)
    stream = StreamingTranscriber(FakeTranscriber(), sample_rate=16000)

    stream.process_chunk(audio, start_offset_sec=0.0)

    assert len(seen) == 1
    assert seen[0] is audio


def test_transcriber_transcribe_reuses_float32_input_for_model_call(monkeypatch) -> None:
    class FakeModel:
        def __init__(self) -> None:
            self.calls: list[np.ndarray] = []

        def transcribe(self, audio, **kwargs):  # type: ignore[no-untyped-def]
            self.calls.append(audio)
            seg = SimpleNamespace(start=0.0, end=1.0, text=" hello ", no_speech_prob=0.1)
            info = SimpleNamespace(language="en")
            return iter([seg]), info

    fake_model = FakeModel()
    transcriber = Transcriber.__new__(Transcriber)
    transcriber._model = fake_model
    transcriber._model_size = "tiny"
    transcriber._process = SimpleNamespace(memory_info=lambda: SimpleNamespace(rss=128 * 1024**2))

    audio = np.linspace(-0.5, 0.5, 1024, dtype=np.float32)
    result = transcriber.transcribe(audio, sample_rate=16000)

    assert len(result) == 1
    assert result[0].text == "hello"
    assert fake_model.calls == [audio]


def test_cli_repeat_listen_and_analyze_lifecycle_smoke(monkeypatch, tmp_path) -> None:
    monkeypatch.setenv("XDG_DATA_HOME", str(tmp_path / "data"))
    monkeypatch.setenv("XDG_RUNTIME_DIR", str(tmp_path / "runtime"))
    (tmp_path / "data" / "voiceforge").mkdir(parents=True, exist_ok=True)

    fake_capture_module = types.ModuleType("voiceforge.audio.capture")
    fake_capture_module.AudioCapture = _FakeAudioCapture
    monkeypatch.setitem(sys.modules, "voiceforge.audio.capture", fake_capture_module)

    ticks = iter([0.0, 2.0, 0.0, 2.0])
    monkeypatch.setattr(main_mod.time, "monotonic", lambda: next(ticks, 2.0))
    monkeypatch.setattr(main_mod.time, "sleep", lambda _seconds: None)

    pipeline_calls: list[int] = []

    def fake_pipeline(
        seconds: int,
        template: str | None = None,
        dry_run: bool = False,
        stream_callback=None,  # type: ignore[no-untyped-def]
    ) -> tuple[str, list[dict[str, object]], dict[str, object]]:
        pipeline_calls.append(seconds)
        idx = len(pipeline_calls)
        return (
            f"analysis-{idx}",
            [{"start_sec": 0.0, "end_sec": 1.0, "speaker": "S1", "text": f"segment-{idx}"}],
            {
                "model": "anthropic/claude-haiku-4-5",
                "questions": [f"q{idx}"],
                "answers": [f"a{idx}"],
                "recommendations": [f"r{idx}"],
                "action_items": [{"description": f"do-{idx}", "assignee": "A"}],
                "cost_usd": 0.0,
            },
        )

    monkeypatch.setattr(main_mod, "run_analyze_pipeline", fake_pipeline)

    for _ in range(2):
        listen_result = runner.invoke(main_mod.app, ["listen", "--duration", "1"])
        assert listen_result.exit_code == 0, listen_result.stdout

    session_ids: list[int] = []
    for seconds in (10, 20):
        analyze_result = runner.invoke(main_mod.app, ["analyze", "--seconds", str(seconds), "--output", "json"])
        assert analyze_result.exit_code == 0, analyze_result.stdout
        session_ids.append(_last_json_line(analyze_result.stdout)["data"]["session_id"])

    history_result = runner.invoke(main_mod.app, ["history", "--last", "10", "--output", "json"])
    assert history_result.exit_code == 0, history_result.stdout
    sessions = _last_json_line(history_result.stdout)["data"]["sessions"]

    assert pipeline_calls == [10, 20]
    assert len(session_ids) == 2
    assert session_ids[0] != session_ids[1]
    assert [session["id"] for session in sessions[:2]] == [session_ids[1], session_ids[0]]
