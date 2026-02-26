"""Block 10.2: Parallel pipeline — Step 1 STT, Step 2 parallel (diarization + RAG + PII), Step 3 LLM."""

from __future__ import annotations

import time
from concurrent.futures import Future, ThreadPoolExecutor, wait
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import numpy as np
import psutil
import structlog

from voiceforge.i18n import t

log = structlog.get_logger()

# #37: skip diarization when available RAM < 2GB to avoid OOM on ≤8GB systems
MIN_AVAILABLE_FOR_DIARIZATION_BYTES = 2 * 1024**3

TARGET_SAMPLE_RATE = 16000  # faster-whisper expects 16 kHz
RAG_QUERY_MAX_CHARS = 1000  # W3: max transcript prefix for RAG search (was 200)


def _resample_to_16k(audio: np.ndarray, from_rate: int) -> np.ndarray:
    """Resample audio to 16 kHz if from_rate != 16000. Returns int16 array."""
    if from_rate == TARGET_SAMPLE_RATE:
        return audio
    try:
        from scipy.signal import resample
    except ImportError:
        log.warning("pipeline.resample_skipped", from_rate=from_rate, hint="Install scipy for resampling")
        return audio
    n = int(len(audio) * TARGET_SAMPLE_RATE / from_rate)
    if n < 1:
        return audio
    out = resample(audio.astype(np.float64), n)
    return (out.clip(-32768, 32767)).astype(np.int16)


@dataclass
class PipelineResult:
    """Result of steps 1–2 (STT + parallel diarization, RAG, PII). Step 3 (LLM) in main."""

    segments: list[Any]  # Transcriber.Segment
    transcript: str
    diar_segments: list[Any]
    context: str
    transcript_redacted: str | None  # None = use redact(transcript) in router


def _step1_stt(
    audio: np.ndarray,
    sample_rate: int,
    model_size: str,
    language_hint: str | None = None,
) -> tuple[list[Any], str]:
    """Step 1: STT only. Returns (segments, transcript). Block 10.4: use ModelManager if set. Language hint for Whisper."""
    from voiceforge.core.model_manager import get_model_manager
    from voiceforge.stt.transcriber import Transcriber

    t0 = time.monotonic()
    manager = get_model_manager()
    if manager is not None:
        transcriber = manager.get_transcriber()
    else:
        transcriber = Transcriber(model_size=model_size)
    segments = transcriber.transcribe(audio, sample_rate=sample_rate, language=language_hint)
    transcript = " ".join(s.text for s in segments if s.text).strip() or t("pipeline.silence")
    duration_sec = time.monotonic() - t0
    log.info("pipeline.step1_stt", segments=len(segments), duration_sec=round(duration_sec, 2))
    try:
        from voiceforge.core.observability import record_stt_duration

        record_stt_duration(duration_sec)
    except ImportError:
        pass
    return (segments, transcript)


def _step2_diarization(
    audio_f: np.ndarray,
    sample_rate: int,
    pyannote_restart_hours: int,
) -> list[Any]:
    """Diarization (pyannote). Runs in thread. Skips if available RAM < 2GB (#37)."""
    t0 = time.monotonic()
    out: list[Any] = []
    try:
        vm = psutil.virtual_memory()
        if vm.available < MIN_AVAILABLE_FOR_DIARIZATION_BYTES:
            log.warning(
                "pipeline.diarization.skipped_low_memory",
                available_mb=round(vm.available / 1024**2, 1),
                threshold_mb=MIN_AVAILABLE_FOR_DIARIZATION_BYTES // (1024**2),
            )
            duration_sec = time.monotonic() - t0
            log.info("pipeline.step2_diarization", count=0, duration_sec=round(duration_sec, 2))
            return out
        try:
            import keyring as _keyring

            auth_token = (_keyring.get_password("voiceforge", "huggingface") or "").strip()
        except Exception:
            auth_token = ""  # nosec B105 -- fallback when keyring unavailable, not a password
        if not auth_token:
            return out
        from voiceforge.stt.diarizer import Diarizer

        diarizer = Diarizer(auth_token=auth_token, restart_hours=pyannote_restart_hours)
        try:
            out = diarizer.diarize(audio_f, sample_rate=sample_rate)
        except MemoryError as e:
            log.warning("pipeline.diarization.oom", error=str(e))
            out = []
        except RuntimeError as e:
            if "out of memory" in str(e).lower():
                log.warning("pipeline.diarization.oom", error=str(e))
                out = []
            else:
                raise
    except ImportError:
        pass
    except Exception as e:
        log.warning("pipeline.diarization.failed", error=str(e))
    duration_sec = time.monotonic() - t0
    log.info("pipeline.step2_diarization", count=len(out), duration_sec=round(duration_sec, 2))
    try:
        from voiceforge.core.observability import record_diarization_duration

        record_diarization_duration(duration_sec)
    except ImportError:
        pass
    return out


def _step2_rag(transcript: str, rag_db_path: str) -> str:
    """RAG search. Runs in thread. C2 (#42): multi-query from transcript segments, merge and dedupe."""
    t0 = time.monotonic()
    context = ""
    try:
        if Path(rag_db_path).is_file():
            from voiceforge.rag.query_keywords import extract_keyword_queries
            from voiceforge.rag.searcher import HybridSearcher

            queries = extract_keyword_queries(transcript)
            if not queries:
                queries = [transcript[:RAG_QUERY_MAX_CHARS] or "meeting"]
            searcher = HybridSearcher(rag_db_path)
            by_id: dict[int, Any] = {}  # chunk_id -> SearchResult (keep higher score)
            for q in queries:
                if not (q and q.strip()):
                    continue
                for r in searcher.search(q, top_k=3):
                    if r.chunk_id not in by_id or r.score > by_id[r.chunk_id].score:
                        by_id[r.chunk_id] = r
            merged = sorted(by_id.values(), key=lambda x: -x.score)[:5]
            context = "\n".join(r.content[:300] for r in merged)
            searcher.close()
    except ImportError:
        pass
    except Exception as e:
        log.warning("pipeline.rag.failed", error=str(e))
    duration_sec = time.monotonic() - t0
    log.info("pipeline.step2_rag", context_len=len(context), duration_sec=round(duration_sec, 2))
    try:
        from voiceforge.core.observability import record_rag_duration

        record_rag_duration(duration_sec)
    except ImportError:
        pass
    return context


def _get_language_hint(cfg: Any) -> str | None:
    """Return language hint for STT from config, or None for auto."""
    lang = getattr(cfg, "language", "auto")
    return lang if lang and lang != "auto" else None


def _step2_pii(transcript: str, pii_mode: str = "ON") -> str:
    """PII redaction. Runs in thread. pii_mode: OFF | ON | EMAIL_ONLY."""
    t0 = time.monotonic()
    try:
        from voiceforge.llm.pii_filter import redact

        out = redact(transcript, mode=pii_mode) or transcript
    except ImportError:
        out = transcript
    except Exception as e:
        log.warning("pipeline.pii.failed", error=str(e))
        out = transcript
    log.info("pipeline.step2_pii", duration_sec=round(time.monotonic() - t0, 2))
    return out


def _prepare_audio(cfg: Any, seconds: int) -> tuple[np.ndarray, int] | tuple[None, str]:
    """Load and resample audio. Returns (audio, effective_rate) or (None, error_str)."""
    ring_path = cfg.get_ring_file_path()
    if not Path(ring_path).is_file():
        return (None, t("pipeline.run_listen_first"))
    raw = Path(ring_path).read_bytes()
    want = int(seconds * cfg.sample_rate * 2)
    if len(raw) > want:
        raw = raw[-want:]
    raw = raw[: len(raw) - (len(raw) % 2)]
    if len(raw) < cfg.sample_rate * 2:
        return (None, t("pipeline.insufficient_audio"))
    audio = np.frombuffer(raw, dtype=np.int16)
    effective_rate = cfg.sample_rate
    if effective_rate != TARGET_SAMPLE_RATE:
        audio = _resample_to_16k(audio, effective_rate)
        effective_rate = TARGET_SAMPLE_RATE
        log.info("pipeline.resampled", original_rate=cfg.sample_rate, target=TARGET_SAMPLE_RATE)
    log.info("pipeline.start", seconds=seconds, samples=len(audio))
    return (audio, effective_rate)


def _step1_or_error(audio: np.ndarray, effective_rate: int, cfg: Any) -> tuple[list[Any], str] | tuple[None, str]:
    """Run STT; return (segments, transcript) or (None, error_str)."""
    language_hint = _get_language_hint(cfg)
    try:
        segments, transcript = _step1_stt(
            audio, sample_rate=effective_rate, model_size=cfg.model_size, language_hint=language_hint
        )
        return (segments, transcript)
    except ImportError:
        try:
            from voiceforge.core.observability import record_pipeline_error

            record_pipeline_error("stt")
        except ImportError:
            pass
        return (None, t("error.install_deps"))
    except Exception as e:
        log.warning("pipeline.step1_failed", error=str(e))
        try:
            from voiceforge.core.observability import record_pipeline_error

            record_pipeline_error("stt")
        except ImportError:
            pass
        return (None, t("error.stt_failed", e=str(e)))


def _gather_step2(
    executor: ThreadPoolExecutor,
    cfg: Any,
    audio_f: np.ndarray,
    transcript: str,
    effective_rate: int,
) -> tuple[list[Any], str, str]:
    """Run step2 parallel tasks; return (diar_segments, context, transcript_redacted)."""
    timeout_sec = max(1.0, float(getattr(cfg, "pipeline_step2_timeout_sec", 25.0)))
    futures: dict[str, Future[Any]] = {
        "diarization": executor.submit(_step2_diarization, audio_f, effective_rate, cfg.pyannote_restart_hours),
        "rag": executor.submit(_step2_rag, transcript, cfg.get_rag_db_path()),
        "pii": executor.submit(_step2_pii, transcript, getattr(cfg, "pii_mode", "ON")),
    }
    done, not_done = wait(futures.values(), timeout=timeout_sec)
    timed_out = [name for name, fut in futures.items() if fut in not_done]
    for name in timed_out:
        futures[name].cancel()
    if timed_out:
        log.warning("pipeline.step2_timeout", timeout_sec=timeout_sec, timed_out=timed_out)
    diar_segments = futures["diarization"].result() if futures["diarization"] in done else []
    context = futures["rag"].result() if futures["rag"] in done else ""
    transcript_redacted = futures["pii"].result() if futures["pii"] in done else transcript
    return (diar_segments, context, transcript_redacted)


def _with_calendar_context(context: str, cfg: Any) -> str:
    """Append calendar context if enabled. D3 (#48)."""
    if not getattr(cfg, "calendar_context_enabled", False):
        return context
    try:
        from voiceforge.calendar.caldav_poll import get_next_meeting_context

        cal_ctx, _ = get_next_meeting_context(hours_ahead=24)
        if cal_ctx:
            return (
                (context + "\n\nCalendar (next meeting): " + cal_ctx).strip()
                if context
                else ("Calendar (next meeting): " + cal_ctx)
            )
    except Exception as e:
        log.warning("pipeline.calendar_context_failed", error=str(e))
    return context


class AnalysisPipeline:
    """Block 10.2: Step 1 STT, Step 2 parallel (diarization + RAG + PII), profiling.
    ThreadPoolExecutor is created once per instance (W15/QW3), use as context manager for cleanup."""

    def __init__(self, cfg: Any) -> None:
        self._cfg = cfg
        self._executor = ThreadPoolExecutor(max_workers=3)

    def __enter__(self) -> AnalysisPipeline:
        return self

    def __exit__(self, *args: Any) -> None:
        self._executor.shutdown(wait=False, cancel_futures=True)

    def run(self, seconds: int) -> tuple[PipelineResult | None, str | None]:
        """Run steps 1–2. Returns (PipelineResult, None) or (None, error_str)."""
        prep = _prepare_audio(self._cfg, seconds)
        if prep[0] is None:
            return (None, prep[1])
        audio, effective_rate = prep
        stt_result = _step1_or_error(audio, effective_rate, self._cfg)
        if stt_result[0] is None:
            return (None, stt_result[1])
        segments, transcript = stt_result
        step2_start = time.monotonic()
        audio_f = audio.astype(np.float32) / 32768.0
        diar_segments, context, transcript_redacted = _gather_step2(
            self._executor, self._cfg, audio_f, transcript, effective_rate
        )
        step2_duration = time.monotonic() - step2_start
        log.info("pipeline.step2_total", duration_sec=round(step2_duration, 2))
        context = _with_calendar_context(context, self._cfg)
        return (
            PipelineResult(
                segments=segments,
                transcript=transcript,
                diar_segments=diar_segments,
                context=context,
                transcript_redacted=transcript_redacted,
            ),
            None,
        )
