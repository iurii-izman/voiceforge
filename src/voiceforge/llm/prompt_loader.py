"""C1 (#41): Prompt management — load prompts from files with versioning."""

from __future__ import annotations

from pathlib import Path

_PROMPTS_DIR = Path(__file__).resolve().parent / "prompts"
_TEMPLATE_NAMES = ("standup", "sprint_review", "one_on_one", "brainstorm", "interview")


def get_prompt_version() -> str | None:
    """Return prompt set version from prompts/version, or None if missing."""
    p = _PROMPTS_DIR / "version"
    if not p.is_file():
        return None
    return p.read_text(encoding="utf-8").strip() or None


def load_prompt(name: str) -> str | None:
    """Load prompt text from prompts/<name>.txt. Return None if file missing."""
    if name.startswith("template_"):
        p = _PROMPTS_DIR / f"{name}.txt"
    else:
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
