"""C1 (#41): Prompt management — load prompts from files with versioning. Block 6 (#67): hash for CI. Phase D #72: custom templates from ~/.config/voiceforge/templates/."""

from __future__ import annotations

import hashlib
import os
from pathlib import Path

_PROMPTS_DIR = Path(__file__).resolve().parent / "prompts"
_TEMPLATE_NAMES = ("standup", "sprint_review", "one_on_one", "brainstorm", "interview")
_SINGLE_PROMPTS = ("analysis", "live_summary", "status_update")


def _user_templates_dir() -> Path:
    """Path to user custom templates (Phase D #72). Override built-in template_*.txt here."""
    base = os.environ.get("XDG_CONFIG_HOME") or os.path.expanduser("~/.config")
    return Path(base) / "voiceforge" / "templates"


def get_prompt_version() -> str | None:
    """Return prompt set version from prompts/version, or None if missing."""
    p = _PROMPTS_DIR / "version"
    if not p.is_file():
        return None
    return p.read_text(encoding="utf-8").strip() or None


def load_prompt(name: str) -> str | None:
    """Load prompt text: for template_* try ~/.config/voiceforge/templates/ first (#72), else prompts/<name>.txt."""
    if name.startswith("template_"):
        user_path = _user_templates_dir() / f"{name}.txt"
        if user_path.is_file():
            return user_path.read_text(encoding="utf-8").strip()
    p = _PROMPTS_DIR / f"{name}.txt"
    if not p.is_file():
        return None
    return p.read_text(encoding="utf-8").strip()


def load_template_prompts() -> dict[str, str] | None:
    """Load all template prompts from prompts/template_*.txt. Return None if any missing."""
    out: dict[str, str] = {}
    for t in _TEMPLATE_NAMES:
        text = load_prompt(f"template_{t}")
        if text is None:
            return None
        out[t] = text
    return out


def get_prompt_hashes() -> dict[str, str]:
    """Return SHA256 hex digest per prompt key (for CI / drift detection). Block 6 (#67)."""
    out: dict[str, str] = {}
    for name in _SINGLE_PROMPTS:
        text = load_prompt(name)
        out[name] = hashlib.sha256((text or "").encode()).hexdigest()
    templates = load_template_prompts()
    if templates:
        for k, text in templates.items():
            out[f"template_{k}"] = hashlib.sha256(text.encode()).hexdigest()
    v = get_prompt_version()
    out["version"] = hashlib.sha256((v or "").encode()).hexdigest()
    return out
