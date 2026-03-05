"""Tests for audio/buffer RingBuffer (#56 coverage)."""

from __future__ import annotations

import numpy as np

from voiceforge.audio.buffer import BYTES_PER_SAMPLE, CHANNELS, SAMPLE_RATE, RingBuffer


def test_ring_buffer_constants() -> None:
    assert SAMPLE_RATE == 16000
    assert CHANNELS == 1
    assert BYTES_PER_SAMPLE == 2


def test_ring_buffer_write_empty_no_op() -> None:
    buf = RingBuffer(maxlen_seconds=1.0)
    buf.write(b"")
    assert buf._total_bytes == 0
    assert len(buf._chunks) == 0


def test_ring_buffer_write_and_read_last() -> None:
    buf = RingBuffer(maxlen_seconds=1.0, sample_rate=8000)
    # 0.5 s at 8000 Hz * 1 ch * 2 bytes = 8000 bytes
    chunk = np.zeros(4000, dtype=np.int16).tobytes()
    buf.write(chunk)
    out = buf.read_last(0.5)
    assert out.dtype == np.int16
    assert len(out) == 4000


def test_ring_buffer_read_last_zero_seconds() -> None:
    buf = RingBuffer(maxlen_seconds=1.0)
    buf.write(np.zeros(100, dtype=np.int16).tobytes())
    out = buf.read_last(0)
    assert out.size == 0


def test_ring_buffer_read_last_empty() -> None:
    buf = RingBuffer(maxlen_seconds=1.0)
    out = buf.read_last(0.5)
    assert out.size == 0


def test_ring_buffer_drops_oldest_when_over_capacity() -> None:
    # 1 s at 16k = 32000 bytes
    buf = RingBuffer(maxlen_seconds=1.0, sample_rate=16000)
    buf.write(b"\x00\x01" * 8000)  # 0.5 s
    buf.write(b"\x00\x02" * 8000)  # another 0.5 s
    buf.write(b"\x00\x03" * 8000)  # total 1.5 s — should drop first 0.5 s
    out = buf.read_last(1.0)
    assert len(out) == 16000
    assert buf._total_bytes <= 32000


def test_ring_buffer_read_last_less_than_stored() -> None:
    buf = RingBuffer(maxlen_seconds=2.0, sample_rate=16000)
    # 1 s = 16000 samples
    buf.write(np.arange(16000, dtype=np.int16).tobytes())
    out = buf.read_last(0.25)  # 0.25 s = 4000 samples
    assert len(out) == 4000
    np.testing.assert_array_equal(out, np.arange(12000, 16000, dtype=np.int16))
