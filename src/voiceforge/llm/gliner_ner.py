"""Optional GLiNER PII detection (PERSON, ADDRESS, ORG). No-op when not installed."""

from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path
from typing import Protocol, cast

PII_LABELS = [
    "PERSON",
    "EMAIL",
    "PHONE",
    "ADDRESS",
    "ORGANIZATION",
    "ID_NUMBER",
    "CREDIT_CARD",
]

MODEL_ID = "urchade/gliner_multi_pii-v1"


@dataclass
class PIIEntity:
    """Detected PII span."""

    start: int
    end: int
    label: str
    text: str


def _model_cache_dir() -> Path:
    base = os.environ.get("XDG_DATA_HOME") or os.path.expanduser("~/.local/share")
    return Path(base) / "voiceforge" / "models" / "gliner_pii"


_class_detector: object | None = None


class _GlinerProtocol(Protocol):
    def predict_entities(self, text: str, labels: list[str], threshold: float = 0.5) -> list[dict]: ...


def _get_detector() -> object | None:
    """Lazy-load GLiNER model (optional). Returns None if gliner not installed."""
    global _class_detector
    if _class_detector is not None:
        return _class_detector
    try:
        from gliner import GLiNER

        cache = _model_cache_dir()
        cache.mkdir(parents=True, exist_ok=True)
        _class_detector = GLiNER.from_pretrained(MODEL_ID, cache_dir=cache)
        return _class_detector
    except ImportError:
        return None
    except Exception:
        return None


def detect(text: str) -> list[PIIEntity]:
    """Detect PII spans. Returns [] if GLiNER not available or on error."""
    if not text or not text.strip():
        return []
    model = _get_detector()
    if model is None:
        return []
    try:
        # Labels: gliner_multi_pii uses these; use uppercase for consistency
        detector = cast(_GlinerProtocol, model)
        entities = detector.predict_entities(text, PII_LABELS, threshold=0.5)
    except Exception:
        return []
    result: list[PIIEntity] = []
    for ent in entities or []:
        label = (ent.get("label") or ent.get("label_")) or "PII"
        if isinstance(label, str):
            label = label.upper().replace(" ", "_")
        sub = (ent.get("text") or "").strip()
        if not sub:
            continue
        start = text.find(sub)
        if start < 0:
            continue
        end = start + len(sub)
        result.append(PIIEntity(start=start, end=end, label=label, text=sub))
    return result
