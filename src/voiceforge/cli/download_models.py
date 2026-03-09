"""E8 (#131): Pre-download Whisper + ONNX embedder with progress and retry."""

from __future__ import annotations

import time

import structlog
from faster_whisper import WhisperModel

from voiceforge.i18n import t
from voiceforge.stt.transcriber import _is_whisper_model_cached

log = structlog.get_logger()

# E4 (#127): approximate sizes MB
WHISPER_SIZE_MB: dict[str, int] = {
    "tiny": 75,
    "base": 142,
    "small": 466,
    "medium": 1500,
    "large": 3000,
    "large-v2": 3000,
    "large-v3": 3000,
    "large-v3-turbo": 3000,
}
MAX_DOWNLOAD_ATTEMPTS = 3
DOWNLOAD_BACKOFF_BASE_SEC = 1.0


def _download_whisper_with_retry(
    model_size: str,
    device: str = "cpu",
    compute_type: str = "int8",
) -> bool:
    """Download Whisper model via faster-whisper with retry on network failure."""

    size_mb = WHISPER_SIZE_MB.get(model_size, 500)
    cached = _is_whisper_model_cached(model_size)
    if cached:
        try:
            model = WhisperModel(model_size, device=device, compute_type=compute_type, local_files_only=True)
            del model
            log.info("download_models.whisper_cached", model_size=model_size, size_mb=size_mb)
            return False
        except Exception as e:
            log.warning("download_models.cached_model_load_failed", model_size=model_size, error=str(e))
    log.info("download_models.whisper_start", model_size=model_size, size_mb=size_mb)
    last_error: Exception | None = None
    for attempt in range(MAX_DOWNLOAD_ATTEMPTS):
        try:
            model = WhisperModel(model_size, device=device, compute_type=compute_type)
            del model  # free memory after cache is populated
            return True
        except Exception as e:
            last_error = e
            if attempt < MAX_DOWNLOAD_ATTEMPTS - 1:
                delay = DOWNLOAD_BACKOFF_BASE_SEC * (2**attempt)
                log.warning(
                    "download_models.whisper_retry",
                    attempt=attempt + 1,
                    error=str(e),
                    retry_sec=delay,
                )
                time.sleep(delay)
    raise last_error


def _ensure_onnx_embedder() -> bool:
    """Ensure ONNX embedder (MiniLM) is loaded if files exist. Returns True if ready."""
    try:
        from pathlib import Path

        from voiceforge.rag.embedder import MiniLMEmbedder, get_default_model_dir

        base = Path(get_default_model_dir())
        if not (base / "model.onnx").exists() and not (base / "onnx" / "model.onnx").exists():
            log.info("download_models.onnx_optional", path=str(base))
            return False
        MiniLMEmbedder(get_default_model_dir())
        return True
    except FileNotFoundError:
        log.info("download_models.onnx_optional", hint="Install/symlink model to get_default_model_dir() for RAG")
        return False
    except ImportError as e:
        log.info("download_models.onnx_skip", reason=str(e))
        return False


def run_download_models(
    model_size: str | None = None,
    skip_onnx: bool = False,
    use_rich_progress: bool = True,
) -> bool:
    """Download Whisper (from config model_size) and optionally warm ONNX embedder. Returns True on success."""
    from voiceforge.core.config import Settings

    cfg = Settings()
    size = (model_size or getattr(cfg, "model_size", "small")).strip() or "small"

    downloaded = False
    if use_rich_progress:
        try:
            from rich.console import Console
            from rich.progress import Progress, SpinnerColumn, TextColumn

            console = Console()
            initially_cached = _is_whisper_model_cached(size)
            with Progress(
                SpinnerColumn(),
                TextColumn("[bold blue]{task.description}"),
                console=console,
            ) as progress:
                task = progress.add_task(
                    t("feedback.model_cached")
                    if initially_cached
                    else t("download_models.whisper_desc", model_size=size, size_mb=WHISPER_SIZE_MB.get(size, 500)),
                    total=None,
                )
                downloaded = _download_whisper_with_retry(size)
                progress.update(task, description=t("feedback.model_ready") if downloaded else t("feedback.model_cached"))
        except ImportError:
            downloaded = _download_whisper_with_retry(size)
    else:
        downloaded = _download_whisper_with_retry(size)

    if not skip_onnx:
        _ensure_onnx_embedder()
    return downloaded
