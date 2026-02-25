"""C2 (#42): Tests for RAG query keyword extraction."""

from voiceforge.rag.query_keywords import extract_keywords


def test_extract_keywords_from_full_transcript() -> None:
    """Long transcript: keywords from end appear in query (full text used, not only prefix)."""
    # Prefix: single-occurrence words; end: repeated so they rank in top_n
    long_transcript = (
        "The meeting started with updates and the team discussed the project. "
        "We went through the backlog and the budget. "
        "Final: договор договор подписан квартальный отчёт отчёт."
    )
    query = extract_keywords(long_transcript, top_n=14)
    # End-of-transcript terms (договор, отчёт repeated) must appear
    assert "договор" in query
    assert "отчёт" in query
    assert query


def test_extract_keywords_empty_returns_empty() -> None:
    """Empty or whitespace transcript returns empty string."""
    assert extract_keywords("") == ""
    assert extract_keywords("   ") == ""


def test_extract_keywords_filters_stopwords() -> None:
    """Common stopwords are not in the result."""
    transcript = "the and in на и что meeting проект"
    query = extract_keywords(transcript)
    assert "the" not in query.split()
    assert "and" not in query.split()
    assert "на" not in query.split()
    assert "meeting" in query or "проект" in query
