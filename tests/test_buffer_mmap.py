"""E18 (#141): Ring file read via mmap (zero-copy tail) and fallback."""

from __future__ import annotations

from pathlib import Path

import numpy as np

from voiceforge.audio.buffer import read_ring_file_last


def test_read_ring_file_last_nonexistent(tmp_path: Path) -> None:
    out = read_ring_file_last(tmp_path / "nonexistent.raw", 1.0)
    assert out.dtype == np.int16
    assert len(out) == 0


def test_read_ring_file_last_empty_file(tmp_path: Path) -> None:
    p = tmp_path / "ring.raw"
    p.write_bytes(b"")
    out = read_ring_file_last(p, 1.0)
    assert len(out) == 0


def test_read_ring_file_last_tail_read(tmp_path: Path) -> None:
    """Last N seconds: 1s at 16kHz = 32000 bytes."""
    p = tmp_path / "ring.raw"
    # 2 seconds of zeros, then 1 second of int16 sequence 0..15999
    two_sec = np.zeros(32000, dtype=np.int16)
    one_sec = np.arange(16000, dtype=np.int16)
    p.write_bytes(two_sec.tobytes() + one_sec.tobytes())
    out = read_ring_file_last(p, 1.0, sample_rate=16000, use_mmap=True)
    assert len(out) == 16000
    np.testing.assert_array_equal(out, one_sec)


def test_read_ring_file_last_fallback_no_mmap(tmp_path: Path) -> None:
    """use_mmap=False uses read_bytes path."""
    p = tmp_path / "ring.raw"
    one_sec = np.arange(16000, dtype=np.int16)
    p.write_bytes(one_sec.tobytes())
    out = read_ring_file_last(p, 1.0, sample_rate=16000, use_mmap=False)
    assert len(out) == 16000
    np.testing.assert_array_equal(out, one_sec)


def test_read_ring_file_last_request_more_than_file(tmp_path: Path) -> None:
    """Request 10s, file has 0.5s — return all."""
    p = tmp_path / "ring.raw"
    half_sec = np.zeros(8000, dtype=np.int16)  # 0.5s at 16kHz
    p.write_bytes(half_sec.tobytes())
    out = read_ring_file_last(p, 10.0, sample_rate=16000)
    assert len(out) == 8000
