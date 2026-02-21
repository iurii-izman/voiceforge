"""ONNX embedder for all-MiniLM-L6-v2 (no PyTorch)."""

from __future__ import annotations

import os
from pathlib import Path

import numpy as np
import structlog

from voiceforge.rag import _onnx_runner

log = structlog.get_logger()

EMBED_DIM = 384
MAX_LENGTH = 256


def _find_model_dir(base: str | Path) -> Path:
    base = Path(base)
    if (base / "model.onnx").exists():
        return base
    if (base / "onnx" / "model.onnx").exists():
        return base / "onnx"
    raise FileNotFoundError(f"No model.onnx in {base} or {base}/onnx")


class MiniLMEmbedder:
    """Embed text with all-MiniLM-L6-v2 via ONNX Runtime."""

    def __init__(self, model_dir: str | Path) -> None:
        self._dir = _find_model_dir(model_dir)
        self._session, self._tokenizer = _onnx_runner.load(self._dir)
        log.info("embedder.loaded", dir=str(self._dir))

    def encode(self, texts: list[str], batch_size: int = 32) -> np.ndarray:
        """Encode texts to (n, 384) float32."""
        if not texts:
            return np.zeros((0, EMBED_DIM), dtype=np.float32)
        out: list[np.ndarray] = []
        for i in range(0, len(texts), batch_size):
            batch = texts[i : i + batch_size]
            emb = _onnx_runner.encode_batch(self._session, self._tokenizer, batch, MAX_LENGTH)
            out.append(emb)
        return np.vstack(out).astype(np.float32)


def get_default_model_dir() -> str:
    base = os.environ.get("XDG_CACHE_HOME") or os.path.expanduser("~/.cache")
    return os.path.join(base, "voiceforge", "minilm-onnx")
