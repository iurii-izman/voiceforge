"""C2 (#42): Keyword extraction for RAG query — use full transcript instead of prefix truncation."""

from __future__ import annotations

import re
from collections import Counter

# Minimal stopwords (ru/en) so content from end of transcript gets into query
_STOP = frozenset(
    {
        "a",
        "an",
        "and",
        "are",
        "as",
        "at",
        "be",
        "by",
        "for",
        "from",
        "has",
        "he",
        "in",
        "is",
        "it",
        "its",
        "of",
        "on",
        "that",
        "the",
        "to",
        "was",
        "were",
        "will",
        "with",
        "и",
        "в",
        "во",
        "не",
        "что",
        "он",
        "на",
        "я",
        "с",
        "со",
        "как",
        "а",
        "то",
        "все",
        "она",
        "так",
        "его",
        "но",
        "да",
        "ты",
        "к",
        "у",
        "же",
        "вы",
        "за",
        "бы",
        "по",
        "только",
        "её",
        "мне",
        "было",
        "вот",
        "от",
        "меня",
        "ещё",
        "нет",
        "о",
        "из",
        "ему",
        "теперь",
        "когда",
        "уже",
        "вам",
        "ни",
        "до",
        "вас",
        "нибудь",
        "опять",
        "уж",
        "там",
        "потом",
        "себя",
        "ничего",
        "ей",
        "им",
        "сегодня",
        "под",
        "где",
        "это",
        "всё",
        "они",
        "мы",
        "чем",
        "или",
        "без",
        "раз",
        "тоже",
        "очень",
    }
)

_MIN_WORD_LEN = 2
_DEFAULT_TOP_N = 12


def extract_keywords(transcript: str, top_n: int = _DEFAULT_TOP_N) -> str:
    """Extract top keywords from full transcript for RAG query (C2 #42).
    Uses word frequency; content from end of transcript is included.
    Returns space-joined keywords, or empty string if none."""
    if not (transcript and transcript.strip()):
        return ""
    words = re.findall(r"[a-zA-Zа-яА-ЯёЁ0-9]+", transcript.lower())
    counts: Counter[str] = Counter()
    for w in words:
        if len(w) >= _MIN_WORD_LEN and w not in _STOP:
            counts[w] += 1
    top = [t[0] for t in counts.most_common(top_n)]
    return " ".join(top).strip()
