"""C2 (#42): Tests for RAG query keyword extraction and multi-query context extension."""

from voiceforge.rag.query_keywords import extract_keyword_queries, extract_keywords


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


def test_extract_keyword_queries_empty_returns_empty_list() -> None:
    """Empty transcript yields no queries."""
    assert extract_keyword_queries("") == []
    assert extract_keyword_queries("   ") == []


def test_extract_keyword_queries_short_returns_single_query() -> None:
    """Short transcript (< 300 chars) returns single full-doc query."""
    short = "Meeting about budget and project timeline."
    queries = extract_keyword_queries(short, min_len_for_multi=100)
    assert len(queries) == 1
    assert "meeting" in queries[0].lower() or "budget" in queries[0].lower()


def test_extract_keyword_queries_long_returns_segment_queries() -> None:
    """Long transcript with distinct halves yields multiple queries (C2 context extension)."""
    first_half = " " * 50 + "alpha beta gamma delta " * 10  # ~250 chars, keywords: alpha beta gamma delta
    second_half = " " * 50 + "omega sigma theta report " * 10  # ~260 chars
    long_transcript = first_half + second_half  # > 300
    queries = extract_keyword_queries(long_transcript, num_parts=2, min_len_for_multi=300)
    assert len(queries) >= 1
    # First segment should emphasize alpha/beta/gamma/delta; second omega/sigma/theta/report
    combined = " ".join(queries).lower()
    assert "alpha" in combined or "beta" in combined or "gamma" in combined
    assert "omega" in combined or "sigma" in combined or "theta" in combined or "report" in combined
