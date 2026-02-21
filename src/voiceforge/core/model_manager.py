"""Block 10.4: Model hot-swap — load/unload/swap STT and LLM without restarting daemon."""

from __future__ import annotations

import gc
from typing import Any

import psutil
import structlog

log = structlog.get_logger()

_instance: Any = None


def get_model_manager() -> Any:
    """Return the global ModelManager instance (set by daemon). None when not running as daemon."""
    return _instance


def set_model_manager(manager: Any) -> None:
    """Set the global ModelManager (daemon calls at startup)."""
    global _instance
    _instance = manager


class ModelManager:
    """Block 10.4: Hot-swap STT and LLM models. load/unload/swap with RSS logging."""

    def __init__(self, cfg: Any) -> None:
        self._cfg = cfg
        self._stt_model_size: str = getattr(cfg, "model_size", "small")
        self._llm_model_id: str = getattr(cfg, "default_llm", "anthropic/claude-haiku-4-5")
        self._transcriber: Any = None

    def get_stt_model_size(self) -> str:
        return self._stt_model_size

    def get_llm_model_id(self) -> str:
        return self._llm_model_id

    def get_transcriber(self) -> Any:
        """Return Transcriber for current STT model (lazy load). Reuse if same size."""
        from voiceforge.stt.transcriber import Transcriber

        if self._transcriber is not None and getattr(self._transcriber, "_model_size", None) == self._stt_model_size:
            return self._transcriber
        self._transcriber = Transcriber(
            model_size=self._stt_model_size,
            compute_type="int8",
            device="cpu",
        )
        return self._transcriber

    def unload_stt(self) -> None:
        """Unload current STT model to free RAM. Log RSS before/after."""
        proc = psutil.Process()
        rss_before = proc.memory_info().rss
        self._transcriber = None
        gc.collect()
        try:
            import torch

            if torch.cuda.is_available():
                torch.cuda.empty_cache()
        except ImportError:
            pass
        rss_after = proc.memory_info().rss
        log.info(
            "model_manager.unload_stt",
            rss_before_mb=round(rss_before / 1024**2, 1),
            rss_after_mb=round(rss_after / 1024**2, 1),
            freed_mb=round((rss_before - rss_after) / 1024**2, 1),
        )

    def swap_stt(self, model_size: str) -> None:
        """Swap STT model: unload current, set new size. Next get_transcriber() loads new model."""
        proc = psutil.Process()
        rss_before = proc.memory_info().rss
        self._transcriber = None
        gc.collect()
        try:
            import torch

            if torch.cuda.is_available():
                torch.cuda.empty_cache()
        except ImportError:
            pass
        old_size = self._stt_model_size
        self._stt_model_size = model_size
        rss_after = proc.memory_info().rss
        log.info(
            "model_manager.swap_stt",
            old=old_size,
            new=model_size,
            rss_before_mb=round(rss_before / 1024**2, 1),
            rss_after_mb=round(rss_after / 1024**2, 1),
        )

    def swap_llm(self, model_id: str) -> None:
        """Swap LLM model id. Next analyze uses new model."""
        old_id = self._llm_model_id
        self._llm_model_id = model_id
        log.info("model_manager.swap_llm", old=old_id, new=model_id)

    def swap_model(self, model_type: str, model_name: str) -> str:
        """Swap by type: 'stt' or 'llm'. Returns 'ok' or error message."""
        model_type = (model_type or "").strip().lower()
        model_name = (model_name or "").strip()
        if not model_name:
            return "error: model_name required"
        if model_type == "stt":
            self.swap_stt(model_name)
            return "ok"
        if model_type == "llm":
            self.swap_llm(model_name)
            return "ok"
        return f"error: unknown model_type '{model_type}' (use stt or llm)"
