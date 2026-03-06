"""Benchmark: RAG query path (keyword extraction, optional embed). Issue #68. Baseline: see tests/baseline_benchmark.json."""

from __future__ import annotations

import pytest
from pytest_benchmark.fixture import BenchmarkFixture

from voiceforge.rag.query_keywords import extract_keyword_queries, extract_keywords


def _long_transcript() -> str:
    """~600 chars for multi-query path."""
    return (
        "The meeting started with updates and the team discussed the project. "
        "We went through the backlog and the budget. "
        "Final: договор договор подписан квартальный отчёт отчёт. "
        "Alpha beta gamma delta " * 8 + "Omega sigma theta report " * 8
    )


@pytest.mark.benchmark
def test_bench_extract_keywords(benchmark: BenchmarkFixture) -> None:
    """extract_keywords on long transcript — pure Python, no DB. Baseline: < 100ms (see baseline_benchmark.json)."""
    text = _long_transcript()

    def run() -> str:
        return extract_keywords(text, top_n=14)

    benchmark(run)


@pytest.mark.benchmark
def test_bench_extract_keyword_queries(benchmark: BenchmarkFixture) -> None:
    """extract_keyword_queries (multi-query) on long transcript. Baseline: < 200ms (see baseline_benchmark.json)."""
    text = _long_transcript()

    def run() -> list[str]:
        return extract_keyword_queries(text, num_parts=3, min_len_for_multi=200)

    benchmark(run)
