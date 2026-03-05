"""Tests for rag.parsers: parse_markdown, parse_txt, parse_html, parse_pdf (when available). #56"""

from __future__ import annotations

import contextlib
from pathlib import Path

import pytest

from voiceforge.rag import parsers


def test_parse_markdown(tmp_path: Path) -> None:
    """parse_markdown strips markdown and returns segments."""
    md = tmp_path / "doc.md"
    md.write_text("# Title\n\nParagraph one.\n\n- item 1\n- item 2\n\n**bold** text.", encoding="utf-8")
    out = parsers.parse_markdown(md)
    assert out
    assert "Title" in " ".join(out) or "Paragraph" in " ".join(out)
    assert "item" in " ".join(out) or "bold" in " ".join(out)


def test_parse_markdown_empty_paragraphs_returns_single_segment(tmp_path: Path) -> None:
    """When only whitespace/code blocks, returns one segment of stripped content."""
    md = tmp_path / "minimal.md"
    md.write_text("Only one line.", encoding="utf-8")
    out = parsers.parse_markdown(md)
    assert out == ["Only one line."]


def test_parse_markdown_missing_file() -> None:
    """parse_markdown raises FileNotFoundError for missing file."""
    with pytest.raises(FileNotFoundError):
        parsers.parse_markdown(Path("/nonexistent/file.md"))


def test_parse_txt(tmp_path: Path) -> None:
    """parse_txt splits by double newline."""
    txt = tmp_path / "doc.txt"
    txt.write_text("First para.\n\nSecond para.\n\nThird.", encoding="utf-8")
    out = parsers.parse_txt(txt)
    assert len(out) >= 2
    assert "First" in out[0]
    assert "Second" in out[1]


def test_parse_txt_single_line(tmp_path: Path) -> None:
    """parse_txt returns one segment for single line."""
    txt = tmp_path / "one.txt"
    txt.write_text("Single line.", encoding="utf-8")
    assert parsers.parse_txt(txt) == ["Single line."]


def test_parse_txt_missing_file() -> None:
    """parse_txt raises FileNotFoundError for missing file."""
    with pytest.raises(FileNotFoundError):
        parsers.parse_txt(Path("/nonexistent/file.txt"))


def test_parse_html(tmp_path: Path) -> None:
    """parse_html extracts text from HTML."""
    html = tmp_path / "page.html"
    html.write_text(
        "<html><body><p>First</p><div>Second</div><h1>Title</h1></body></html>",
        encoding="utf-8",
    )
    out = parsers.parse_html(html)
    assert out
    joined = " ".join(out)
    assert "First" in joined
    assert "Second" in joined or "Title" in joined


def test_parse_html_missing_file() -> None:
    """parse_html raises FileNotFoundError for missing file."""
    with pytest.raises(FileNotFoundError):
        parsers.parse_html(Path("/nonexistent/file.html"))


def test_parse_pdf_missing_file() -> None:
    """parse_pdf raises FileNotFoundError for missing file."""
    with pytest.raises(FileNotFoundError):
        parsers.parse_pdf(Path("/nonexistent/file.pdf"))


def test_parse_pdf_import_error_when_no_pymupdf(tmp_path: Path) -> None:
    """parse_pdf raises ImportError when pymupdf not installed (existing file triggers import)."""
    pdf = tmp_path / "dummy.pdf"
    pdf.write_bytes(b"not a pdf")
    try:
        import fitz  # noqa: F401
        # With pymupdf, fitz.open may raise on invalid content
        with contextlib.suppress(Exception):
            parsers.parse_pdf(pdf)
    except ImportError:
        with pytest.raises(ImportError, match="rag|pymupdf"):
            parsers.parse_pdf(pdf)


def test_parse_docx_missing_file() -> None:
    """parse_docx raises FileNotFoundError for missing file."""
    with pytest.raises(FileNotFoundError):
        parsers.parse_docx(Path("/nonexistent/file.docx"))
