"""Deduplication: cosine similarity > threshold => duplicate."""

from __future__ import annotations

import numpy as np

DEFAULT_COSINE_THRESHOLD = 0.95


def cosine_similarity(a: np.ndarray, b: np.ndarray) -> float:
    """Single pair; a and b are 1d float32."""
    a = a.astype(np.float64)
    b = b.astype(np.float64)
    n = np.linalg.norm(a) * np.linalg.norm(b)
    if n == 0:
        return 0.0
    return float(np.dot(a, b) / n)


def is_duplicate(
    embedding: np.ndarray,
    existing: np.ndarray,
    threshold: float = DEFAULT_COSINE_THRESHOLD,
) -> bool:
    """True if embedding is cosine-similar to any row in existing above threshold."""
    if existing.size == 0:
        return False
    if embedding.ndim == 1:
        embedding = embedding.reshape(1, -1)
    # Normalize
    en = embedding / (np.linalg.norm(embedding, axis=1, keepdims=True) + 1e-9)
    ex = existing.astype(np.float64)
    ex_norm = np.linalg.norm(ex, axis=1, keepdims=True)
    ex_norm[ex_norm == 0] = 1
    ex = ex / ex_norm
    sims = np.dot(en, ex.T).ravel()
    return bool(np.any(sims >= threshold))
