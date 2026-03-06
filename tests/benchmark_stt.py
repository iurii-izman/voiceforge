"""Benchmark: STT transcription on fixture WAV. Issue #68. Baseline: see tests/baseline_benchmark.json."""

from __future__ import annotations

import wave
from pathlib import Path

import numpy as np
import pytest
from pytest_benchmark.fixture import BenchmarkFixture

from voiceforge.stt.transcriber import Transcriber

FIXTURES_DIR = Path(__file__).resolve().parent / "fixtures"


def _load_wav(path: Path) -> tuple[np.ndarray, int]:
    with wave.open(str(path), "rb") as w:
        rate = w.getframerate()
        n = w.getnframes()
        buf = w.readframes(n)
    return np.frombuffer(buf, dtype=np.int16), rate


@pytest.mark.benchmark
@pytest.mark.slow
def test_bench_stt_silence_5s(benchmark: BenchmarkFixture) -> None:
    """STT on silence_5s.wav (5s) — baseline for regression."""
    path = FIXTURES_DIR / "silence_5s.wav"
    if not path.exists():
        pytest.skip("fixture missing: run scripts/gen_stt_fixtures.py")
    audio, rate = _load_wav(path)
    transcriber = Transcriber(model_size="tiny")

    def run() -> None:
        transcriber.transcribe(audio, sample_rate=rate)

    benchmark(run)
    # Baseline (approximate): tiny model on 5s silence < 30s; see baseline_benchmark.json. Optional: assert in CI.
