"""Unit tests for RAG parsers (ODT, RTF). Roadmap 18: tests when adding ODT/RTF (#29)."""

from pathlib import Path

import pytest


def test_parse_rtf_extracts_text(tmp_path: Path) -> None:
    """parse_rtf returns segments from minimal RTF content."""
    rtf = tmp_path / "sample.rtf"
    rtf.write_bytes(b"{\\rtf1\\ansi Hello from RTF.}")
    from voiceforge.rag.parsers import parse_rtf

    segments = parse_rtf(rtf)
    assert len(segments) >= 1
    assert "Hello" in segments[0] or "Hello from RTF" in " ".join(segments)


def test_parse_odt_extracts_text(tmp_path: Path) -> None:
    """parse_odt returns segments from ODT with paragraphs."""
    from odf import text as odf_text
    from odf.opendocument import OpenDocumentText

    odt = tmp_path / "sample.odt"
    doc = OpenDocumentText()
    p = odf_text.P()
    p.addText("Hello from ODT.")
    doc.text.addElement(p)
    doc.save(str(odt))

    from voiceforge.rag.parsers import parse_odt

    segments = parse_odt(odt)
    assert len(segments) >= 1
    assert "Hello from ODT" in " ".join(segments)


def test_parse_rtf_missing_file_raises(tmp_path: Path) -> None:
    """parse_rtf raises FileNotFoundError for non-existent path."""
    from voiceforge.rag.parsers import parse_rtf

    missing = tmp_path / "missing.rtf"
    assert not missing.exists()
    with pytest.raises(FileNotFoundError):
        parse_rtf(missing)


def test_parse_odt_missing_file_raises(tmp_path: Path) -> None:
    """parse_odt raises FileNotFoundError for non-existent path."""
    from voiceforge.rag.parsers import parse_odt

    missing = tmp_path / "missing.odt"
    assert not missing.exists()
    with pytest.raises(FileNotFoundError):
        parse_odt(missing)


def test_parse_rtf_empty_content_returns_segments(tmp_path: Path) -> None:
    """parse_rtf returns list (empty or single segment) for minimal RTF with no text."""
    from voiceforge.rag.parsers import parse_rtf

    rtf = tmp_path / "empty.rtf"
    rtf.write_bytes(b"{\\rtf1\\ansi }")
    segments = parse_rtf(rtf)
    assert isinstance(segments, list)
