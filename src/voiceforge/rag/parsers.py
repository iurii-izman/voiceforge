"""Block 5.4: Multi-format parsers — PDF, MD, HTML, DOCX, TXT. Returns list of text segments."""

from __future__ import annotations

import re
from html.parser import HTMLParser
from pathlib import Path


def parse_pdf(path: str | Path) -> list[str]:
    """Extract text per page from PDF. Requires pymupdf."""
    path = Path(path)
    if not path.is_file():
        raise FileNotFoundError(str(path))
    try:
        import fitz  # PyMuPDF
    except ImportError:
        raise ImportError("Install [rag]: uv sync --extra rag (pymupdf)") from None
    doc = fitz.open(path)
    out: list[str] = []
    for i in range(len(doc)):
        out.append(doc[i].get_text().strip())
    doc.close()
    return out


def parse_markdown(path: str | Path) -> list[str]:
    """Read file, return text segments (strip markdown: headers, lists, code via regex)."""
    path = Path(path)
    if not path.is_file():
        raise FileNotFoundError(str(path))
    raw = path.read_text(encoding="utf-8", errors="replace")
    # Remove code blocks first (keep content)
    raw = re.sub(r"```[\s\S]*?```", " ", raw)
    raw = re.sub(r"`[^`]+`", " ", raw)
    # Headers: drop # and keep line
    raw = re.sub(r"^#{1,6}\s*", "", raw, flags=re.MULTILINE)
    # List markers
    raw = re.sub(r"^\s*[-*+]\s+", "", raw, flags=re.MULTILINE)
    raw = re.sub(r"^\s*\d+\.\s+", "", raw, flags=re.MULTILINE)
    # Bold/italic
    raw = re.sub(r"\*\*([^*]+)\*\*", r"\1", raw)
    raw = re.sub(r"\*([^*]+)\*", r"\1", raw)
    raw = re.sub(r"__([^_]+)__", r"\1", raw)
    raw = re.sub(r"_([^_]+)_", r"\1", raw)
    # Split by double newline (paragraphs)
    segments = [p.strip() for p in raw.split("\n\n") if p.strip()]
    if segments:
        return segments
    stripped = raw.strip()
    if stripped:
        return [stripped]
    return []


class _TextExtractor(HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self.text: list[str] = []
        self._current: list[str] = []

    def handle_data(self, data: str) -> None:
        self._current.append(data)

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        block_tags = ("p", "div", "br", "li", "h1", "h2", "h3", "h4", "h5", "h6", "tr")
        if tag in block_tags and self._current:
            self.text.append(" ".join(self._current).strip())
            self._current = []

    def handle_endtag(self, tag: str) -> None:
        if tag in ("p", "div", "li", "h1", "h2", "h3", "h4", "h5", "h6") and self._current:
            self.text.append(" ".join(self._current).strip())
            self._current = []


def parse_html(path: str | Path) -> list[str]:
    """Extract text segments from HTML via stdlib html.parser."""
    path = Path(path)
    if not path.is_file():
        raise FileNotFoundError(str(path))
    raw = path.read_text(encoding="utf-8", errors="replace")
    parser = _TextExtractor()
    parser.feed(raw)
    if parser._current:
        parser.text.append(" ".join(parser._current).strip())
    segments = [s for s in parser.text if s]
    if segments:
        return segments
    stripped = raw.strip()
    if stripped:
        return [stripped]
    return []


def parse_txt(path: str | Path) -> list[str]:
    """Split file by paragraphs (double newline or single)."""
    path = Path(path)
    if not path.is_file():
        raise FileNotFoundError(str(path))
    raw = path.read_text(encoding="utf-8", errors="replace")
    segments = [p.strip() for p in re.split(r"\n\s*\n", raw) if p.strip()]
    if segments:
        return segments
    stripped = raw.strip()
    if stripped:
        return [stripped]
    return []


def parse_docx(path: str | Path) -> list[str]:
    """Extract paragraphs from DOCX. Requires python-docx (optional in [rag])."""
    path = Path(path)
    if not path.is_file():
        raise FileNotFoundError(str(path))
    try:
        from docx import Document
    except ImportError:
        raise ImportError("Install [rag] with python-docx: uv sync --extra rag") from None
    doc = Document(str(path))
    segments = [p.text.strip() for p in doc.paragraphs if p.text.strip()]
    return segments if segments else []


def parse_odt(path: str | Path) -> list[str]:
    """Extract text from ODT (OpenDocument Text). Requires odfpy (optional in [rag])."""
    path = Path(path)
    if not path.is_file():
        raise FileNotFoundError(str(path))
    try:
        from odf import teletype, text
        from odf.opendocument import load
    except ImportError:
        raise ImportError("Install [rag] with odfpy: uv sync --extra rag") from None
    doc = load(str(path))
    segments: list[str] = []
    for el in doc.getElementsByType(text.P):
        t = teletype.extractText(el).strip()
        if t:
            segments.append(t)
    for el in doc.getElementsByType(text.H):
        t = teletype.extractText(el).strip()
        if t:
            segments.append(t)
    if not segments:
        for el in doc.getElementsByType(text.Span):
            t = teletype.extractText(el).strip()
            if t:
                segments.append(t)
    return segments if segments else []


def parse_rtf(path: str | Path) -> list[str]:
    """Extract plain text from RTF. Requires striprtf (optional in [rag])."""
    path = Path(path)
    if not path.is_file():
        raise FileNotFoundError(str(path))
    try:
        from striprtf.striprtf import rtf_to_text
    except ImportError:
        raise ImportError("Install [rag] with striprtf: uv sync --extra rag") from None
    raw = path.read_bytes()
    try:
        text_content = rtf_to_text(raw.decode("utf-8", errors="replace"))
    except Exception:
        text_content = rtf_to_text(raw.decode("cp1252", errors="replace"))
    segments = [p.strip() for p in re.split(r"\n\s*\n", text_content) if p.strip()]
    return segments if segments else ([text_content.strip()] if text_content.strip() else [])
