"""Unit tests for RAG parsers (ODT, RTF)."""

from pathlib import Path


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
