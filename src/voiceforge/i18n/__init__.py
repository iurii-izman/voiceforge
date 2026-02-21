"""Block 11.4: i18n — t(key), get_locale(), config language: auto | ru | en."""

from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any

_DEFAULT_LOCALE = "ru"
_FALLBACK_LOCALE = "en"
_translations: dict[str, dict[str, str]] = {}
_locale: str | None = None


def _i18n_dir() -> Path:
    return Path(__file__).resolve().parent


def _load_locale(lang: str) -> dict[str, str]:
    if lang in _translations:
        return _translations[lang]
    path = _i18n_dir() / f"{lang}.json"
    if not path.is_file():
        return {}
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
        _translations[lang] = dict(data) if isinstance(data, dict) else {}
        return _translations[lang]
    except Exception:
        return {}


def get_locale() -> str:
    """Current locale: ru or en. Resolved from config language (auto → LANG/LC_ALL) or explicit."""
    global _locale
    if _locale is not None:
        return _locale
    try:
        from voiceforge.core.config import Settings

        cfg = Settings()
        lang = (getattr(cfg, "language", None) or "auto").strip().lower()
    except Exception:
        lang = "auto"
    if lang in ("ru", "en"):
        _locale = lang
        return _locale
    # auto: from env
    lc = (os.environ.get("LANG") or os.environ.get("LC_ALL") or "").strip().lower()
    if lc.startswith("ru"):
        _locale = "ru"
    elif lc.startswith("en"):
        _locale = "en"
    else:
        _locale = _DEFAULT_LOCALE
    return _locale


def set_locale(lang: str) -> None:
    """Set current locale (ru or en). Used by config and tests."""
    global _locale
    _locale = lang if lang in ("ru", "en") else _DEFAULT_LOCALE


def t(key: str, **kwargs: Any) -> str:
    """Translate key for current locale. Fallback: en → ru → key. Use {placeholder} in JSON and kwargs."""
    loc = get_locale()
    for candidate in (loc, _FALLBACK_LOCALE, _DEFAULT_LOCALE):
        strings = _load_locale(candidate)
        if key in strings:
            s = strings[key]
            if kwargs:
                try:
                    s = s.format(**kwargs)
                except KeyError:
                    pass
            return s
    return key.format(**kwargs) if kwargs else key
