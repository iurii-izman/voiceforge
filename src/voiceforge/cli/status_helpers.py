"""Status helpers extracted from main CLI module."""

from __future__ import annotations

import importlib
from pathlib import Path
from typing import Any

_DOCTOR_KEYRING_FAIL = "doctor.keyring_fail"
_DOCTOR_OLLAMA_FAIL = "doctor.ollama_fail"
_DOCTOR_RAM_FAIL = "doctor.ram_fail"


def get_status_text() -> str:
    """Return status string (RAM + cost + Ollama + PII) for CLI or D-Bus."""
    import psutil

    from voiceforge.core.config import Settings
    from voiceforge.core.metrics import get_cost_today
    from voiceforge.i18n import t

    mem = psutil.virtual_memory()
    cost = get_cost_today()
    used_gb = mem.used / 1024**3
    total_gb = mem.total / 1024**3
    cfg = Settings()
    lines = [
        t("status.ram", used=used_gb, total=total_gb, percent=mem.percent),
        t("status.cost_today", cost=cost),
        t("status.pii_mode", mode=getattr(cfg, "pii_mode", "ON")),
    ]
    try:
        from voiceforge.llm.local_llm import is_available

        lines.append(t("status.ollama_available") if is_available() else t("status.ollama_unavailable"))
    except ImportError:
        lines.append(t("status.ollama_unavailable"))
    return "\n".join(lines)


def get_status_data() -> dict[str, Any]:
    """Return machine-readable status data (includes pii_mode for PII UX)."""
    import psutil

    from voiceforge.core.config import Settings
    from voiceforge.core.metrics import get_cost_today

    mem = psutil.virtual_memory()
    ollama_available = False
    try:
        from voiceforge.llm.local_llm import is_available

        ollama_available = bool(is_available())
    except ImportError:
        ollama_available = False
    cfg = Settings()
    return {
        "ram": {
            "used_gb": round(mem.used / 1024**3, 2),
            "total_gb": round(mem.total / 1024**3, 2),
            "percent": float(mem.percent),
        },
        "cost_today_usd": round(float(get_cost_today()), 6),
        "pii_mode": getattr(cfg, "pii_mode", "ON"),
        "ollama_available": ollama_available,
    }


def _format_stats_block(data: dict, budget_limit_usd: float, label: str) -> list[str]:
    """Format one block of stats (by_model, by_day, rate) for status --detailed."""
    lines: list[str] = []
    total = data.get("total_cost_usd") or 0
    pct = (total / budget_limit_usd * 100) if budget_limit_usd > 0 else 0
    lines.append(f"Затраты за {label}: ${total:.4f} ({pct:.1f}% от бюджета ${budget_limit_usd:.0f})")
    for e in data.get("by_model") or []:
        lines.append(f"  {e.get('model', '')}: ${(e.get('cost_usd') or 0):.4f} ({e.get('calls', 0)} вызовов)")
    by_day = data.get("by_day") or []
    if by_day:
        lines.append("  По дням:")
        for row in by_day[-7:]:
            lines.append(f"    {row.get('date', '')}: ${(row.get('cost_usd') or 0):.4f}")
    rate = data.get("response_cache_hit_rate")
    if rate is not None:
        lines.append(f"  Cache hit rate: {rate * 100:.1f}%")
    return lines


def get_status_detailed_text(budget_limit_usd: float) -> str:
    """Return multi-line status with cost by model/day, cache hit rate, budget % (for status --detailed)."""
    from voiceforge.core.metrics import get_stats

    lines: list[str] = [get_status_text(), ""]
    for days, label in [(7, "7 дней"), (30, "30 дней")]:
        lines.extend(_format_stats_block(get_stats(days=days), budget_limit_usd, label))
        lines.append("")
    return "\n".join(lines).rstrip()


def get_status_detailed_data(budget_limit_usd: float) -> dict[str, Any]:
    """Return detailed status dict: stats_7d, stats_30d, budget_limit_usd (for status --detailed --output json)."""
    from voiceforge.core.metrics import get_stats

    base = get_status_data()
    base["budget_limit_usd"] = budget_limit_usd
    base["stats_7d"] = get_stats(days=7)
    base["stats_30d"] = get_stats(days=30)
    return base


def _doctor_check_keyring(t: Any) -> tuple[bool, str, str]:
    try:
        import keyring
        from keyring.errors import KeyringError

        found = []
        for name in ("anthropic", "openai", "huggingface"):
            try:
                if keyring.get_password("voiceforge", name):
                    found.append(name)
            except KeyringError:
                pass
        return (
            (True, t("doctor.keyring_ok"), "doctor.keyring_ok")
            if found
            else (False, t(_DOCTOR_KEYRING_FAIL), _DOCTOR_KEYRING_FAIL)
        )
    except Exception as e:
        return (False, f"keyring: {e}", _DOCTOR_KEYRING_FAIL)


def _doctor_check_rag_ring(cfg: Any, t: Any) -> list[tuple[bool, str, str]]:
    out: list[tuple[bool, str, str]] = []
    if Path(cfg.get_rag_db_path()).exists():
        out.append((True, t("doctor.rag_ok"), "doctor.rag_ok"))
    else:
        out.append((True, t("doctor.rag_optional"), "doctor.rag_optional"))
    if Path(cfg.get_ring_file_path()).exists():
        out.append((True, t("doctor.ring_ok"), "doctor.ring_ok"))
    else:
        out.append((False, t("doctor.ring_absent"), "doctor.ring_absent"))
    return out


def _doctor_check_ollama(t: Any) -> tuple[bool, str, str]:
    try:
        from voiceforge.llm.local_llm import is_available

        return (
            (True, t("doctor.ollama_ok"), "doctor.ollama_ok")
            if is_available()
            else (True, t(_DOCTOR_OLLAMA_FAIL), _DOCTOR_OLLAMA_FAIL)
        )
    except ImportError:
        return (True, t(_DOCTOR_OLLAMA_FAIL), _DOCTOR_OLLAMA_FAIL)


def _doctor_check_ram(t: Any) -> tuple[bool, str, str]:
    try:
        import psutil

        gb = psutil.virtual_memory().available / 1024**3
        return (
            (True, t("doctor.ram_ok", gb=gb), "doctor.ram_ok")
            if gb >= 2.0
            else (False, t(_DOCTOR_RAM_FAIL, gb=gb), _DOCTOR_RAM_FAIL)
        )
    except Exception:
        return (False, "RAM check failed", _DOCTOR_RAM_FAIL)


def _doctor_check_module(mod: str, t: Any) -> tuple[bool, str, str]:
    try:
        importlib.import_module(mod.replace("-", "_"))
        key = "doctor.llm_ok" if mod == "litellm" else "doctor.stt_ok"
        return (True, t(key), key)
    except Exception:
        key = "doctor.llm_fail" if mod == "litellm" else "doctor.stt_fail"
        return (False, t(key), key)


def _doctor_checks() -> list[tuple[bool, str, str]]:
    """Run doctor checks. Returns list of (ok: bool, message: str, i18n_key: str)."""
    from voiceforge.core.config import Settings
    from voiceforge.i18n import t

    cfg = Settings()
    results: list[tuple[bool, str, str]] = [(True, t("doctor.config_ok"), "doctor.config_ok")]
    results.append(_doctor_check_keyring(t))
    results.extend(_doctor_check_rag_ring(cfg, t))
    results.append(_doctor_check_ollama(t))
    results.append(_doctor_check_ram(t))
    for mod in ("litellm", "faster_whisper"):
        results.append(_doctor_check_module(mod, t))
    return results


def get_doctor_text() -> str:
    """Return doctor diagnostic lines (✓/✗ + message)."""
    lines = []
    for ok, msg, _ in _doctor_checks():
        lines.append(f"  {'✓' if ok else '✗'} {msg}")
    return "\n".join(lines)


def get_doctor_data() -> dict[str, Any]:
    """Return doctor checks as machine-readable list."""
    checks = []
    for ok, msg, key in _doctor_checks():
        checks.append({"ok": ok, "message": msg, "key": key})
    return {"checks": checks, "errors": sum(1 for c in checks if not c["ok"])}
