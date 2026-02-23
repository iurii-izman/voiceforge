"""Block 10.1: Chunk-based streaming STT — reuse Transcriber, 2s chunks, 0.5s overlap, callbacks."""

from __future__ import annotations

from collections import deque
from collections.abc import Callable
from dataclasses import dataclass

import numpy as np
import structlog

from voiceforge.stt.transcriber import Segment, Transcriber

log = structlog.get_logger()

TARGET_SAMPLE_RATE = 16000  # faster-whisper expects 16 kHz (W2: resample when capture rate differs)


def _resample_float_to_16k(audio_f: np.ndarray, from_rate: int) -> tuple[np.ndarray, int]:
    """Resample float32 mono audio to 16 kHz. Returns (audio_float32, TARGET_SAMPLE_RATE) or (input, from_rate) on failure."""
    if from_rate == TARGET_SAMPLE_RATE:
        return (audio_f, TARGET_SAMPLE_RATE)
    try:
        from scipy.signal import resample
    except ImportError:
        log.warning(
            "streaming.resample_skipped",
            from_rate=from_rate,
            hint="Install scipy for resampling; quality may degrade",
        )
        return (audio_f, from_rate)
    n = int(len(audio_f) * TARGET_SAMPLE_RATE / from_rate)
    if n < 1:
        return (audio_f, from_rate)
    out = resample(audio_f.astype(np.float64), n).astype(np.float32)
    return (out, TARGET_SAMPLE_RATE)


# Chunk 2s, overlap 0.5s → step 1.5s (latency ~2s for first partial)
CHUNK_DURATION_SEC = 2.0
CHUNK_OVERLAP_SEC = 0.5
CHUNK_STEP_SEC = CHUNK_DURATION_SEC - CHUNK_OVERLAP_SEC


@dataclass
class StreamingSegment:
    """Segment with optional stream offset (same as Segment for compatibility)."""

    start: float
    end: float
    text: str
    language: str | None
    confidence: float


def _segment_from_transcriber(s: Segment) -> StreamingSegment:
    return StreamingSegment(
        start=s.start,
        end=s.end,
        text=s.text,
        language=s.language,
        confidence=s.confidence,
    )


class StreamingTranscriber:
    """Chunk-based streaming using existing Transcriber (one model, no extra RAM).
    Buffer: 2s chunks with 0.5s overlap. Callbacks: on_partial(text), on_final(segment).
    Latency target: partial/final within ~2s of speech."""

    def __init__(
        self,
        transcriber: Transcriber,
        sample_rate: int = 16000,
        chunk_duration_sec: float = CHUNK_DURATION_SEC,
        overlap_sec: float = CHUNK_OVERLAP_SEC,
        *,
        language: str | None = None,
        on_partial: Callable[[str], None] | None = None,
        on_final: Callable[[StreamingSegment], None] | None = None,
    ) -> None:
        self._transcriber = transcriber
        self._sample_rate = sample_rate
        self._language = language
        self._chunk_duration = chunk_duration_sec
        self._overlap = overlap_sec
        self._step_sec = chunk_duration_sec - overlap_sec
        self._on_partial = on_partial or (lambda _: None)
        self._on_final = on_final or (lambda _: None)
        self._buffer: deque[tuple[np.ndarray, float]] = deque()  # (samples, start_time)
        self._buffer_duration = 0.0
        self._stream_time = 0.0

    def feed(self, audio: np.ndarray) -> None:
        """Append audio (int16 or float32, mono). Flush when buffer >= chunk_duration."""
        if audio.size == 0:
            return
        if audio.dtype == np.int16:
            audio = audio.astype(np.float32) / 32768.0
        else:
            audio = audio.astype(np.float32).copy()
        dur = audio.size / self._sample_rate
        self._buffer.append((audio, self._stream_time))
        self._buffer_duration += dur
        self._stream_time += dur
        while self._buffer_duration >= self._chunk_duration:
            self._flush_chunk()

    def _flush_chunk(self) -> None:
        """Take chunk_duration from buffer, transcribe, emit; then push back overlap for next window."""
        if not self._buffer:
            return
        want_samples = int(self._chunk_duration * self._sample_rate)
        overlap_samples = int(self._overlap * self._sample_rate)
        chunks: list[np.ndarray] = []
        taken = 0
        start_time = self._buffer[0][1]
        while self._buffer and taken < want_samples:
            block, t0 = self._buffer.popleft()
            self._buffer_duration -= block.size / self._sample_rate
            need = want_samples - taken
            if block.size <= need:
                chunks.append(block)
                taken += block.size
            else:
                head = block[:need]
                rest = block[need:]
                chunks.append(head)
                taken += need
                self._buffer.appendleft((rest, t0 + need / self._sample_rate))
                self._buffer_duration += rest.size / self._sample_rate
                break
        if not chunks:
            return
        chunk = np.concatenate(chunks) if len(chunks) > 1 else chunks[0]
        eff: int | None = None
        if self._sample_rate != TARGET_SAMPLE_RATE:
            chunk, eff = _resample_float_to_16k(chunk, self._sample_rate)
        self._process_chunk(chunk, start_time, effective_rate=eff)
        # Push back last overlap_sec so next window overlaps
        if overlap_samples > 0 and chunk.size >= overlap_samples:
            tail = chunk[-overlap_samples:]
            overlap_time = start_time + self._step_sec
            self._buffer.appendleft((tail, overlap_time))
            self._buffer_duration += self._overlap

    def _process_chunk(
        self,
        audio: np.ndarray,
        start_offset_sec: float = 0.0,
        effective_rate: int | None = None,
    ) -> None:
        """Transcribe one chunk and call on_partial / on_final for each segment."""
        if audio.size < 100:  # too short
            return
        rate = effective_rate if effective_rate is not None else self._sample_rate
        segments = self._transcriber.transcribe(
            audio,
            sample_rate=rate,
            language=self._language,
            beam_size=1,
            vad_filter=True,
        )
        for s in segments:
            seg = _segment_from_transcriber(s)
            seg = StreamingSegment(
                start=seg.start + start_offset_sec,
                end=seg.end + start_offset_sec,
                text=seg.text,
                language=seg.language,
                confidence=seg.confidence,
            )
            if seg.text:
                self._on_partial(seg.text)
                self._on_final(seg)
        if segments:
            log.debug("streaming.chunk_done", segments=len(segments), start_offset=start_offset_sec)

    def process_chunk(self, audio: np.ndarray, start_offset_sec: float = 0.0) -> None:
        """Process a pre-cut chunk (e.g. last 2s from ring buffer). No internal buffering.
        Use from listen/daemon: get_chunk(2) → process_chunk(mic).
        W2: when sample_rate != 16 kHz, resample to 16k before transcribe."""
        if audio.size == 0:
            return
        if audio.dtype == np.int16:
            audio = audio.astype(np.float32) / 32768.0
        else:
            audio = audio.astype(np.float32).copy()
        effective_rate: int | None = None
        if self._sample_rate != TARGET_SAMPLE_RATE:
            audio, effective_rate = _resample_float_to_16k(audio, self._sample_rate)
        self._process_chunk(audio, start_offset_sec, effective_rate=effective_rate)
