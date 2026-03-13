"""KC5 (#177): Evidence-first RAG — groundedness, citations, no-KB fallback."""

from __future__ import annotations

from voiceforge.rag.groundedness import (
    THRESHOLD_GROUNDED,
    THRESHOLD_SEMI_GROUNDED,
    confidence_from_results,
    format_evidence_citations,
    get_conflict_hint,
)
from voiceforge.rag.searcher import SearchResult


def _make_result(chunk_id: int, content: str, source: str, page: int, score: float) -> SearchResult:
    return SearchResult(
        chunk_id=chunk_id,
        content=content,
        source=source,
        page=page,
        chunk_index=0,
        timestamp="",
        score=score,
    )


def test_confidence_from_results_no_db_returns_no_kb() -> None:
    """When has_rag_db is False, level is no_kb and confidence 0."""
    level, norm = confidence_from_results([], has_rag_db=False)
    assert level == "no_kb"
    assert norm == 0.0

    level2, norm2 = confidence_from_results([_make_result(1, "x", "a.pdf", 1, 0.05)], has_rag_db=False)
    assert level2 == "no_kb"
    assert norm2 == 0.0


def test_confidence_from_results_empty_results_returns_ungrounded() -> None:
    """When has_rag_db True but no results, level is ungrounded."""
    level, norm = confidence_from_results([], has_rag_db=True)
    assert level == "ungrounded"
    assert norm == 0.0


def test_confidence_from_results_grounded_when_above_threshold() -> None:
    """When best score > THRESHOLD_GROUNDED, level is grounded."""
    score = THRESHOLD_GROUNDED + 0.01
    level, norm = confidence_from_results([_make_result(1, "a", "doc.pdf", 1, score)], has_rag_db=True)
    assert level == "grounded"
    assert 0.5 <= norm <= 1.0


def test_confidence_from_results_semi_grounded_in_range() -> None:
    """When best score in [THRESHOLD_SEMI_GROUNDED, THRESHOLD_GROUNDED], level is semi_grounded."""
    score = (THRESHOLD_SEMI_GROUNDED + THRESHOLD_GROUNDED) / 2
    level, norm = confidence_from_results([_make_result(1, "a", "doc.pdf", 1, score)], has_rag_db=True)
    assert level == "semi_grounded"
    assert 0 <= norm <= 1.0


def test_confidence_from_results_ungrounded_below_semi() -> None:
    """When best score < THRESHOLD_SEMI_GROUNDED, level is ungrounded."""
    level, norm = confidence_from_results([_make_result(1, "a", "doc.pdf", 1, 0.005)], has_rag_db=True)
    assert level == "ungrounded"
    assert 0 <= norm < 0.5


def test_format_evidence_citations_basename_and_page() -> None:
    """Citations include source_basename and page."""
    results = [
        _make_result(1, "First chunk content here.", "/path/to/Pricing_v5.pdf", 7, 0.04),
        _make_result(2, "Second chunk.", "/other/SLA.pdf", 2, 0.03),
    ]
    citations = format_evidence_citations(results, max_sources=3)
    assert len(citations) == 2
    assert citations[0]["source_basename"] == "Pricing_v5.pdf"
    assert citations[0]["page"] == 7
    assert citations[0]["chunk_id"] == 1
    assert "First chunk" in citations[0]["snippet"]
    assert citations[1]["source_basename"] == "SLA.pdf"
    assert citations[1]["page"] == 2


def test_format_evidence_citations_respects_max_sources() -> None:
    """At most max_sources entries returned."""
    results = [_make_result(i, f"content {i}", f"doc{i}.pdf", i, 0.04 - i * 0.001) for i in range(5)]
    citations = format_evidence_citations(results, max_sources=2)
    assert len(citations) == 2


def test_get_conflict_hint_none_for_single_source() -> None:
    """No conflict hint when only one source."""
    results = [
        _make_result(1, "a", "/p/doc.pdf", 1, 0.04),
        _make_result(2, "b", "/p/doc.pdf", 2, 0.035),
    ]
    assert get_conflict_hint(results) is None


def test_get_conflict_hint_returns_message_when_multiple_sources() -> None:
    """Conflict hint when two distinct sources with similar scores."""
    results = [
        _make_result(1, "a", "/p/doc1.pdf", 1, 0.04),
        _make_result(2, "b", "/p/doc2.pdf", 2, 0.038),
    ]
    hint = get_conflict_hint(results)
    assert hint is not None
    assert "different" in hint.lower() or "consistent" in hint.lower()


def test_short_capture_query_extraction() -> None:
    """Short transcript uses single-query path (for_short_capture / SHORT_CAPTURE_MAX_CHARS)."""
    from voiceforge.rag.query_keywords import (
        extract_keyword_queries,
    )

    short = "What is the enterprise price?"
    queries = extract_keyword_queries(short, for_short_capture=True)
    assert len(queries) == 1
    assert "enterprise" in queries[0] or "price" in queries[0]

    queries2 = extract_keyword_queries(short)  # len(short) < 400
    assert len(queries2) == 1
