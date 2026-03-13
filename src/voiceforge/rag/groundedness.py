"""KC5 (#177): Evidence-first RAG — groundedness classification and citations.

Groundedness levels per voiceforge-copilot-architecture.md §7:
- grounded: RRF score > 0.03
- semi_grounded: 0.01 <= score <= 0.03
- ungrounded: score < 0.01 or no results
- no_kb: RAG DB missing or not used
"""

from __future__ import annotations

from pathlib import Path
from typing import Any, Literal

from voiceforge.rag.searcher import SearchResult

# Thresholds from architecture doc §7 Confidence scoring
THRESHOLD_GROUNDED = 0.03
THRESHOLD_SEMI_GROUNDED = 0.01

GroundednessLevel = Literal["grounded", "semi_grounded", "ungrounded", "no_kb"]


def confidence_from_results(
    results: list[SearchResult],
    has_rag_db: bool,
) -> tuple[GroundednessLevel, float]:
    """Classify groundedness from RAG search results.

    Returns (level, normalized_confidence in 0..1 for display).
    When has_rag_db is False or results empty due to no DB, returns ("no_kb", 0.0).
    """
    if not has_rag_db:
        return ("no_kb", 0.0)
    if not results:
        return ("ungrounded", 0.0)
    best_score = max(r.score for r in results)
    if best_score > THRESHOLD_GROUNDED:
        level: GroundednessLevel = "grounded"
        # Normalize to 0.5–1.0 for grounded
        norm = 0.5 + min(0.5, (best_score - THRESHOLD_GROUNDED) / 0.05)
    elif best_score >= THRESHOLD_SEMI_GROUNDED:
        level = "semi_grounded"
        norm = 0.25 + (best_score - THRESHOLD_SEMI_GROUNDED) / (THRESHOLD_GROUNDED - THRESHOLD_SEMI_GROUNDED) * 0.25
    else:
        level = "ungrounded"
        norm = best_score / THRESHOLD_SEMI_GROUNDED * 0.25
    return (level, min(1.0, max(0.0, norm)))


def _source_basename(source: str) -> str:
    """Return basename of source path for citation display."""
    return Path(source).name if source else ""


def format_evidence_citations(
    results: list[SearchResult],
    max_sources: int = 3,
    snippet_max_chars: int = 200,
) -> list[dict[str, Any]]:
    """Format search results as evidence citations: source basename, page, snippet.

    Returns list of dicts with keys: source_basename, page, chunk_id, snippet.
    """
    out: list[dict[str, Any]] = []
    seen: set[tuple[str, int]] = set()
    for r in results:
        if len(out) >= max_sources:
            break
        key = (_source_basename(r.source), r.page)
        if key in seen:
            continue
        seen.add(key)
        snippet = (r.content or "").strip()
        if len(snippet) > snippet_max_chars:
            snippet = snippet[:snippet_max_chars].rsplit(maxsplit=1)[0] + "…"
        out.append(
            {
                "source_basename": _source_basename(r.source),
                "page": r.page,
                "chunk_id": r.chunk_id,
                "snippet": snippet,
            }
        )
    return out


def get_conflict_hint(results: list[SearchResult]) -> str | None:
    """If multiple distinct sources with similar scores might conflict, return user-visible hint.

    Heuristic: 2+ results from different source files with close top scores.
    """
    if len(results) < 2:
        return None
    top_score = results[0].score
    sources = {_source_basename(r.source) for r in results if r.score >= top_score * 0.7}
    if len(sources) >= 2:
        return "Sources from different documents; check if information is consistent."
    return None
