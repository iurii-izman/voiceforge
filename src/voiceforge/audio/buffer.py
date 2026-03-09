"""Ring buffer for raw PCM s16le. E18: optional mmap for ring file read."""

from __future__ import annotations

import mmap
from collections import deque
from pathlib import Path

import numpy as np

SAMPLE_RATE = 16000
CHANNELS = 1
BYTES_PER_SAMPLE = 2


def read_ring_file_last(
    path: Path | str,
    seconds: float,
    sample_rate: int = SAMPLE_RATE,
    use_mmap: bool = True,
) -> np.ndarray:
    """Read last N seconds from ring.raw. Uses mmap for zero-copy tail when use_mmap and file is large enough; else fallback to read_bytes."""
    path = Path(path)
    if not path.is_file():
        return np.array([], dtype=np.int16)
    want_bytes = int(seconds * sample_rate * CHANNELS * BYTES_PER_SAMPLE)
    file_size = path.stat().st_size
    if file_size == 0:
        return np.array([], dtype=np.int16)
    want_bytes = min(want_bytes, file_size - (file_size % 2))
    if want_bytes <= 0:
        return np.array([], dtype=np.int16)
    if use_mmap and file_size >= want_bytes:
        try:
            with open(path, "rb") as f:
                mm = mmap.mmap(f.fileno(), 0, access=mmap.ACCESS_READ)
                try:
                    start = file_size - want_bytes
                    data = mm[start:file_size]
                    return np.frombuffer(bytes(data), dtype=np.int16)
                finally:
                    mm.close()
        except (OSError, ValueError, TypeError):
            pass
    raw = path.read_bytes()
    if len(raw) > want_bytes:
        raw = raw[-want_bytes:]
    raw = raw[: len(raw) - (len(raw) % 2)]
    if not raw:
        return np.array([], dtype=np.int16)
    return np.frombuffer(raw, dtype=np.int16)


class RingBuffer:
    """Fixed-size buffer (in seconds). Stores raw s16le bytes."""

    def __init__(self, maxlen_seconds: float, sample_rate: int = SAMPLE_RATE) -> None:
        self._sample_rate = sample_rate
        self._maxlen_bytes = int(maxlen_seconds * sample_rate * CHANNELS * BYTES_PER_SAMPLE)
        self._chunks: deque[bytes] = deque()
        self._total_bytes = 0

    def write(self, data: bytes) -> None:
        """Append chunk; oldest data beyond maxlen is dropped."""
        if not data:
            return
        self._chunks.append(data)
        self._total_bytes += len(data)
        while self._total_bytes > self._maxlen_bytes and self._chunks:
            old = self._chunks.popleft()
            self._total_bytes -= len(old)

    def read_last(self, seconds: float) -> np.ndarray:
        """Return last N seconds as int16 numpy array (mono). Thread-safe: snapshot of deque to avoid 'deque mutated during iteration' when capture thread writes."""
        want_bytes = int(seconds * self._sample_rate * CHANNELS * BYTES_PER_SAMPLE)
        total = self._total_bytes
        if want_bytes <= 0 or total == 0:
            return np.array([], dtype=np.int16)
        want_bytes = min(want_bytes, total)
        collected: list[bytes] = []
        remaining = want_bytes
        snapshot = list(self._chunks)
        for chunk in reversed(snapshot):
            if remaining <= 0:
                break
            take = min(remaining, len(chunk))
            collected.append(chunk[-take:])
            remaining -= take
        if not collected:
            return np.array([], dtype=np.int16)
        data = b"".join(reversed(collected))
        return np.frombuffer(data, dtype=np.int16)
