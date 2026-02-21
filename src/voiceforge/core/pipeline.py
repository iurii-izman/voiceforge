"""Block 10.2: Parallel pipeline — Step 1 STT, Step 2 parallel (diarization + RAG + PII), Step 3 LLM."""

from __future__ import annotations

import time
from concurrent.futures import Future, ThreadPoolExecutor, wait
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import numpy as np
import structlog

log = structlog.get_logger()


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
) -> tuple[list[Any], str]:
    """Step 1: STT only. Returns (segments, transcript). Block 10.4: use ModelManager if set."""
    from voiceforge.core.model_manager import get_model_manager
    from voiceforge.stt.transcriber import Transcriber

    t0 = time.monotonic()
    manager = get_model_manager()
    if manager is not None:
        transcriber = manager.get_transcriber()
    else:
        transcriber = Transcriber(model_size=model_size)
    segments = transcriber.transcribe(audio, sample_rate=sample_rate)
    transcript = " ".join(s.text for s in segments if s.text).strip() or "(тишина)"
    log.info("pipeline.step1_stt", segments=len(segments), duration_sec=round(time.monotonic() - t0, 2))
    return (segments, transcript)


def _step2_diarization(
    audio_f: np.ndarray,
    sample_rate: int,
    pyannote_restart_hours: int,
) -> list[Any]:
    """Diarization (pyannote). Runs in thread."""
    t0 = time.monotonic()
    out: list[Any] = []
    try:
        try:
            import keyring as _keyring

            auth_token = (_keyring.get_password("voiceforge", "huggingface") or "").strip()
        except Exception:
            auth_token = ""
        if not auth_token:
            return out
        from voiceforge.stt.diarizer import Diarizer

        diarizer = Diarizer(auth_token=auth_token, restart_hours=pyannote_restart_hours)
        out = diarizer.diarize(audio_f, sample_rate=sample_rate)
    except ImportError:
        pass
    except Exception as e:
        log.warning("pipeline.diarization.failed", error=str(e))
    log.info("pipeline.step2_diarization", count=len(out), duration_sec=round(time.monotonic() - t0, 2))
    return out


def _step2_rag(transcript: str, rag_db_path: str) -> str:
    """RAG search. Runs in thread."""
    t0 = time.monotonic()
    context = ""
    try:
        if Path(rag_db_path).is_file():
            from voiceforge.rag.searcher import HybridSearcher

            searcher = HybridSearcher(rag_db_path)
            results = searcher.search(transcript[:200] or "meeting", top_k=3)
            context = "\n".join(r.content[:300] for r in results)
            searcher.close()
    except ImportError:
        pass
    except Exception as e:
        log.warning("pipeline.rag.failed", error=str(e))
    log.info("pipeline.step2_rag", context_len=len(context), duration_sec=round(time.monotonic() - t0, 2))
    return context


def _step2_pii(transcript: str) -> str:
    """PII redaction. Runs in thread."""
    t0 = time.monotonic()
    try:
        from voiceforge.llm.pii_filter import redact

        out = redact(transcript) or transcript
    except ImportError:
        out = transcript
    except Exception as e:
        log.warning("pipeline.pii.failed", error=str(e))
        out = transcript
    log.info("pipeline.step2_pii", duration_sec=round(time.monotonic() - t0, 2))
    return out


class AnalysisPipeline:
    """Block 10.2: Step 1 STT, Step 2 parallel (diarization + RAG + PII), profiling."""

    def __init__(self, cfg: Any) -> None:
        self._cfg = cfg

    def run(self, seconds: int) -> tuple[PipelineResult | None, str | None]:
        """Run steps 1–2. Returns (PipelineResult, None) or (None, error_str)."""
        ring_path = self._cfg.get_ring_file_path()
        if not Path(ring_path).is_file():
            return (None, "Ошибка: сначала запустите voiceforge listen.")
        raw = Path(ring_path).read_bytes()
        want = int(seconds * self._cfg.sample_rate * 2)
        if len(raw) > want:
            raw = raw[-want:]
        raw = raw[: len(raw) - (len(raw) % 2)]
        if len(raw) < self._cfg.sample_rate * 2:
            return (None, "Ошибка: недостаточно аудио в буфере.")
        audio = np.frombuffer(raw, dtype=np.int16)
        log.info("pipeline.start", seconds=seconds, samples=len(audio))

        try:
            segments, transcript = _step1_stt(
                audio,
                sample_rate=self._cfg.sample_rate,
                model_size=self._cfg.model_size,
            )
        except ImportError:
            return (None, "Ошибка: установите зависимости (uv sync).")
        except Exception as e:
            log.warning("pipeline.step1_failed", error=str(e))
            return (None, f"Ошибка STT: {e}")

        audio_f = audio.astype(np.float32) / 32768.0
        diar_segments: list[Any] = []
        context = ""
        transcript_redacted = transcript

        step2_start = time.monotonic()
        timeout_sec = max(1.0, float(getattr(self._cfg, "pipeline_step2_timeout_sec", 25.0)))
        executor = ThreadPoolExecutor(max_workers=3)
        try:
            futures: dict[str, Future[Any]] = {
                "diarization": executor.submit(
                    _step2_diarization,
                    audio_f,
                    self._cfg.sample_rate,
                    self._cfg.pyannote_restart_hours,
                ),
                "rag": executor.submit(
                    _step2_rag,
                    transcript,
                    self._cfg.get_rag_db_path(),
                ),
                "pii": executor.submit(_step2_pii, transcript),
            }

            done, not_done = wait(futures.values(), timeout=timeout_sec)
            timed_out = [name for name, fut in futures.items() if fut in not_done]
            for name in timed_out:
                futures[name].cancel()
            if timed_out:
                log.warning(
                    "pipeline.step2_timeout",
                    timeout_sec=timeout_sec,
                    timed_out=timed_out,
                )

            if "diarization" in futures and futures["diarization"] in done:
                diar_segments = futures["diarization"].result()
            if "rag" in futures and futures["rag"] in done:
                context = futures["rag"].result()
            if "pii" in futures and futures["pii"] in done:
                transcript_redacted = futures["pii"].result()
        finally:
            executor.shutdown(wait=False, cancel_futures=True)
        step2_duration = time.monotonic() - step2_start
        log.info("pipeline.step2_total", duration_sec=round(step2_duration, 2))

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
