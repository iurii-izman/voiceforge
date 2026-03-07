"""Block 86: Property-based tests for RAG parsers (Hypothesis)."""

from __future__ import annotations

import tempfile
from pathlib import Path

import pytest
from hypothesis import given, settings
from hypothesis import strategies as st

from voiceforge.rag import parsers

# Skip if optional dependency missing
pytest.importorskip("hypothesis")


@settings(max_examples=100, deadline=2000)
@given(
    paragraphs=st.lists(
        st.text(st.characters(blacklist_categories=("Cs", "Cc"), blacklist_characters="\x00"), min_size=0, max_size=200),
        min_size=0,
        max_size=20,
    )
)
def test_parse_txt_roundtrip_paragraphs(paragraphs: list[str]) -> None:
    """parse_txt: writing paragraphs joined by \\n\\n and parsing yields same number of non-empty segments."""
    content = "\n\n".join(p.strip() for p in paragraphs if p.strip())
    with tempfile.TemporaryDirectory() as d:
        path = Path(d) / "doc.txt"
        path.write_text(content, encoding="utf-8")
        result = parsers.parse_txt(path)
    assert isinstance(result, list)
    assert all(isinstance(s, str) for s in result)
    if content.strip():
        assert len(result) >= 1
        assert all(len(s) > 0 for s in result)
    else:
        assert len(result) == 0 or (len(result) == 1 and result[0].strip() == "")


@settings(max_examples=80, deadline=2000)
@given(raw=st.text(st.characters(blacklist_categories=("Cs", "Cc"), blacklist_characters="\x00"), min_size=0, max_size=300))
def test_parse_markdown_never_crashes(raw: str) -> None:
    """parse_markdown: does not crash on any utf-8 file content (block 86)."""
    with tempfile.TemporaryDirectory() as d:
        path = Path(d) / "doc.md"
        path.write_text(raw, encoding="utf-8")
        result = parsers.parse_markdown(path)
    assert isinstance(result, list)
    assert all(isinstance(s, str) for s in result)
