"""C1 (#41): Tests for prompt_loader — load from prompts/ with snapshot guard."""

from __future__ import annotations

import hashlib

from voiceforge.llm.prompt_loader import (
    get_prompt_version,
    load_prompt,
    load_template_prompts,
)


def _hash(s: str | None) -> str:
    return hashlib.sha256((s or "").encode()).hexdigest()


def test_load_prompt_returns_non_empty_for_known_names() -> None:
    """All known prompt names load non-empty content from prompts/."""
    for name in ("analysis", "live_summary", "status_update"):
        text = load_prompt(name)
        assert text is not None, f"load_prompt({name!r}) should not be None"
        assert len(text) > 50, f"load_prompt({name!r}) should have substantial content"
        assert "meeting" in text.lower() or "transcript" in text.lower(), (
            f"load_prompt({name!r}) should mention meeting/transcript"
        )


def test_load_template_prompts_returns_all() -> None:
    """Template prompts load for all 5 templates."""
    prompts = load_template_prompts()
    assert prompts is not None
    assert set(prompts) == {"standup", "sprint_review", "one_on_one", "brainstorm", "interview"}
    for key, text in prompts.items():
        assert text, f"template {key} should be non-empty"
        assert len(text) > 20


def test_get_prompt_version() -> None:
    """Version file is read or None if missing."""
    v = get_prompt_version()
    # In repo we have prompts/version with content
    assert v is None or isinstance(v, str)
    if v is not None:
        assert v.strip() == v


def test_prompt_content_snapshot() -> None:
    """Snapshot: loaded prompt content hashes. Fails if prompts/ files change unintentionally."""
    expected = {
        "analysis": "a8cb497aa82788a6e4d348dbf8aeb840ef07593a6df757ad4eababaa396d2198",
        "live_summary": "62e43fcbc4fbddbf8664a9fbdcc3912364c202bc4b28cd78a05b6e35b0b87d06",
        "status_update": "aa9cbc03a212e87c2d9aa84caa02f657fc509be0636399fb1ddf0d1bb475b26f",
        "template_brainstorm": "3d421419ecf582170164e54489664c14f7fada8c4398f81b02e483fef7a7a2b9",
        "template_interview": "014d050ec06d7684a0c43866d2e4e29f1b0e3f9c342448497a5d9b0208210a77",
        "template_one_on_one": "8a8451fc2fda142dbe8c5585d4ca6aac95b70c9479ab0fded44c3ff81acd83fa",
        "template_sprint_review": "a8c1ecf64a5c46ef8bba370b7c52e4305e8a0ca3e4420ef728fa02b02327e507",
        "template_standup": "b36b89a9d9b84ecbb2ef5989ba64846b138249ac733f087d5944b613cb425b44",
        "version": "6b86b273ff34fce19d6b804eff5a3f5747ada4eaa22f1d49c01e52ddb7875b4b",
    }
    actual: dict[str, str] = {}
    for name in ("analysis", "live_summary", "status_update"):
        text = load_prompt(name)
        actual[name] = _hash(text)
    templates = load_template_prompts()
    assert templates is not None
    for k, text in templates.items():
        actual[f"template_{k}"] = _hash(text)
    actual["version"] = _hash(get_prompt_version())
    for key in expected:
        assert actual[key] == expected[key], (
            f"Prompt {key} content changed. Update expected hash in this test if change is intentional."
        )
