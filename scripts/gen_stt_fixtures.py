#!/usr/bin/env python3
"""Generate WAV fixtures for STT integration tests (16 kHz, mono, int16)."""

from pathlib import Path

import numpy as np


def write_wav(path: Path, samples: np.ndarray, sample_rate: int = 16000) -> None:
    """Write int16 mono WAV file."""
    import wave

    path.parent.mkdir(parents=True, exist_ok=True)
    with wave.open(str(path), "wb") as w:
        w.setnchannels(1)
        w.setsampwidth(2)
        w.setframerate(sample_rate)
        w.writeframes(samples.astype(np.int16).tobytes())


def main() -> None:
    base = Path(__file__).resolve().parent.parent / "tests" / "fixtures"
    base.mkdir(parents=True, exist_ok=True)
    rate = 16000

    # 5 s silence
    write_wav(base / "silence_5s.wav", np.zeros(rate * 5, dtype=np.int16), rate)
    # 5 s and 30 s silence for "clean" placeholder (replace with real speech for WER tests)
    write_wav(base / "clean_5s.wav", np.zeros(rate * 5, dtype=np.int16), rate)
    write_wav(base / "clean_30s.wav", np.zeros(rate * 30, dtype=np.int16), rate)
    print("Generated:", list(base.glob("*.wav")))


if __name__ == "__main__":
    main()
