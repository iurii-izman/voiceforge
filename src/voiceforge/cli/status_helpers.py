"""Status helpers extracted from main CLI module."""

from __future__ import annotations

from typing import Any


def get_status_text() -> str:
    """Return status string (RAM + cost + Ollama) for CLI or D-Bus."""
    import psutil

    from voiceforge.core.metrics import get_cost_today
    from voiceforge.i18n import t

    mem = psutil.virtual_memory()
    cost = get_cost_today()
    used_gb = mem.used / 1024**3
    total_gb = mem.total / 1024**3
    lines = [
        t("status.ram", used=used_gb, total=total_gb, percent=mem.percent),
        t("status.cost_today", cost=cost),
    ]
    try:
        from voiceforge.llm.local_llm import is_available

        lines.append(t("status.ollama_available") if is_available() else t("status.ollama_unavailable"))
    except ImportError:
        lines.append(t("status.ollama_unavailable"))
    return "\n".join(lines)


def get_status_data() -> dict[str, Any]:
    """Return machine-readable status data."""
    import psutil

    from voiceforge.core.metrics import get_cost_today

    mem = psutil.virtual_memory()
    ollama_available = False
    try:
        from voiceforge.llm.local_llm import is_available

        ollama_available = bool(is_available())
    except ImportError:
        ollama_available = False
    return {
        "ram": {
            "used_gb": round(mem.used / 1024**3, 2),
            "total_gb": round(mem.total / 1024**3, 2),
            "percent": float(mem.percent),
        },
        "cost_today_usd": round(float(get_cost_today()), 6),
        "ollama_available": ollama_available,
    }
