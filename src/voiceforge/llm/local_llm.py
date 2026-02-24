"""Block 5.2: Local LLM via Ollama — classify and simple_answer ($0).
Phi-3 Mini 4bit ~2.5 GB RAM."""

from __future__ import annotations

import json
import os
import urllib.error
import urllib.parse
import urllib.request
from typing import Literal

import structlog

log = structlog.get_logger()


def _ollama_base() -> str:
    base = os.environ.get("OLLAMA_HOST", "http://localhost:11434")
    normalized = base.rstrip("/") if base.startswith("http") else f"http://{base}"
    parsed = urllib.parse.urlparse(normalized)
    if parsed.scheme not in {"http", "https"} or not parsed.netloc:
        return "http://localhost:11434"
    return normalized


DEFAULT_MODEL = "phi3:mini"
CLASSIFY_TIMEOUT = 8
GENERATE_TIMEOUT = 30
Classification = Literal["code", "faq", "multilang", "analysis"]


def _ollama_request(path: str, data: dict, timeout: float = 10) -> dict | None:
    base = _ollama_base()
    try:
        req = urllib.request.Request(
            f"{base}{path}",
            data=json.dumps(data).encode("utf-8"),
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        with urllib.request.urlopen(req, timeout=timeout) as resp:  # nosec B310  # nosemgrep: python.lang.security.audit.dynamic-urllib-use-detected.dynamic-urllib-use-detected
            return json.loads(resp.read().decode())
    except (urllib.error.URLError, json.JSONDecodeError, OSError) as e:  # NOSONAR S5713
        log.debug("ollama.request_failed", path=path, error=str(e))
        return None


def is_available(timeout: float = 2.0) -> bool:
    """Return True if Ollama is running (GET /api/tags or /api/version)."""
    try:
        req = urllib.request.Request(f"{_ollama_base()}/api/tags", method="GET")
        with urllib.request.urlopen(req, timeout=timeout) as _:  # nosec B310  # nosemgrep: python.lang.security.audit.dynamic-urllib-use-detected.dynamic-urllib-use-detected
            return True
    except Exception:  # NOSONAR S5713
        return False


def classify(text: str, model: str = DEFAULT_MODEL) -> Classification:
    """Classify transcript into: code | faq | multilang | analysis.
    Uses Ollama; on failure returns 'analysis'."""
    if not text or not text.strip():
        return "analysis"
    prompt = (
        "Classify the following meeting/transcript snippet into exactly one category. "
        "Reply with only one word: code, faq, multilang, or analysis. "
        "code = programming/code discussion. faq = simple Q&A or short factual questions. "
        "multilang = multiple languages. analysis = complex meeting needing full analysis.\n\n"
        f"Snippet:\n{text[:1500]}"
    )
    out = _ollama_request(
        "/api/chat",
        {"model": model, "messages": [{"role": "user", "content": prompt}], "stream": False},
        timeout=CLASSIFY_TIMEOUT,
    )
    if not out:
        return "analysis"
    content = (out.get("message") or {}).get("content") or ""
    word = content.strip().lower().split()[0] if content.strip() else ""
    if word in ("code", "faq", "multilang", "analysis"):
        log.info("ollama.classify", result=word)
        return word  # type: ignore[return-value]
    return "analysis"


def simple_answer(question: str, context: str, model: str = DEFAULT_MODEL) -> str:
    """Answer briefly using context. For FAQ-style queries without API call. Returns plain text."""
    if not question.strip():
        return ""
    user = (
        f"Context:\n{context[:2000]}\n\nQuestion or transcript excerpt:\n{question[:1500]}\n\n"
        "Answer briefly in the same language."
    )
    out = _ollama_request(
        "/api/chat",
        {"model": model, "messages": [{"role": "user", "content": user}], "stream": False},
        timeout=GENERATE_TIMEOUT,
    )
    if not out:
        return ""
    return ((out.get("message") or {}).get("content") or "").strip()
