"""Ring buffer for raw PCM s16le."""

from collections import deque

import numpy as np

SAMPLE_RATE = 16000
CHANNELS = 1
BYTES_PER_SAMPLE = 2


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
        """Return last N seconds as int16 numpy array (mono)."""
        want_bytes = int(seconds * self._sample_rate * CHANNELS * BYTES_PER_SAMPLE)
        if want_bytes <= 0 or self._total_bytes == 0:
            return np.array([], dtype=np.int16)
        want_bytes = min(want_bytes, self._total_bytes)
        collected: list[bytes] = []
        remaining = want_bytes
        for chunk in reversed(self._chunks):
            if remaining <= 0:
                break
            take = min(remaining, len(chunk))
            collected.append(chunk[-take:])
            remaining -= take
        if not collected:
            return np.array([], dtype=np.int16)
        data = b"".join(reversed(collected))
        return np.frombuffer(data, dtype=np.int16)
