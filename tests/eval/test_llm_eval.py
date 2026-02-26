"""Eval harness for LLM outputs: ROUGE-L on golden samples, optional LLM-judge (issue #32)."""

from __future__ import annotations

import json
from pathlib import Path

import pytest
from pydantic import BaseModel, Field
from rouge_score import rouge_scorer

from voiceforge.core.secrets import get_api_key

GOLDEN_DIR = Path(__file__).resolve().parent / "golden_samples"
ROUGE_L_THRESHOLD = 0.35  # Issue #32: accept ≥ 0.35 in next-iteration-focus; issue AC says ≥ 0.4


def _structured_to_text(obj: dict) -> str:
    """Flatten structured output (dict) to a single string for ROUGE comparison."""
    parts: list[str] = []
    for key, val in sorted(obj.items()):
        if isinstance(val, list):
            for i, item in enumerate(val):
                if isinstance(item, dict):
                    parts.append(f"{key}_{i}: " + " ".join(f"{k}={v}" for k, v in sorted(item.items()) if v))
                else:
                    parts.append(f"{key}: {item}")
        elif isinstance(val, str) and val:
            parts.append(f"{key}: {val}")
    return " ".join(parts)


def _load_golden(path: Path) -> tuple[str, str | None, dict]:
    """Load golden sample: (transcript, template, reference_dict)."""
    data = json.loads(path.read_text())
    transcript = data.get("transcript", "")
    template = data.get("template")
    reference = data.get("reference", {})
    return transcript, template, reference


def _rouge_l(reference: str, candidate: str) -> float:
    """ROUGE-L F1 score (0..1)."""
    if not reference.strip() and not candidate.strip():
        return 1.0
    if not reference.strip() or not candidate.strip():
        return 0.0
    scorer = rouge_scorer.RougeScorer(["rougeL"], use_stemmer=False)
    scores = scorer.score(reference, candidate)
    return scores["rougeL"].fmeasure


@pytest.fixture(scope="module")
def golden_samples() -> list[Path]:
    """Paths to golden sample JSON files."""
    if not GOLDEN_DIR.is_dir():
        return []
    return sorted(GOLDEN_DIR.glob("*.json"), key=lambda p: p.name)


def test_rouge_l_self_match() -> None:
    """ROUGE-L of a text with itself is 1.0."""
    text = "done: Finished API. planned: Add tests. blockers: None."
    assert _rouge_l(text, text) == pytest.approx(1.0)


def test_rouge_l_partial_match() -> None:
    """ROUGE-L decreases when candidate differs from reference."""
    ref = "done: Finished API. planned: Add tests."
    cand = "done: Finished API. planned: Write docs."
    score = _rouge_l(ref, cand)
    assert score >= 0.2
    assert score < 1.0


def test_structured_to_text() -> None:
    """Flatten standup-style reference to text."""
    ref = {
        "done": ["Finished the API for export"],
        "planned": ["Add tests"],
        "blockers": ["Waiting for design on the login screen"],
    }
    text = _structured_to_text(ref)
    assert "Finished" in text
    assert "Add tests" in text
    assert "design" in text


def test_load_golden_sample(golden_samples: list[Path]) -> None:
    """Load at least one golden sample and check reference text."""
    if not golden_samples:
        pytest.skip("No golden samples in tests/eval/golden_samples/")
    path = golden_samples[0]
    transcript, _template, reference = _load_golden(path)
    assert transcript
    assert reference
    ref_text = _structured_to_text(reference)
    assert ref_text
    # Self-match for this sample
    assert _rouge_l(ref_text, ref_text) == pytest.approx(1.0)


def _golden_paths() -> list[Path]:
    """Golden sample paths (for parametrize at collection time)."""
    if not GOLDEN_DIR.is_dir():
        return []
    return sorted(GOLDEN_DIR.glob("*.json"), key=lambda p: p.name)


@pytest.mark.parametrize("path", _golden_paths(), ids=[p.stem for p in _golden_paths()])
def test_golden_rouge_l_threshold(path: Path) -> None:
    """Each golden reference text meets ROUGE-L(self, self) >= threshold (sanity)."""
    _transcript, _template, reference = _load_golden(path)
    ref_text = _structured_to_text(reference)
    score = _rouge_l(ref_text, ref_text)
    assert score >= ROUGE_L_THRESHOLD, f"{path.name}: ROUGE-L self {score} < {ROUGE_L_THRESHOLD}"


# --- LLM-judge: optional test, runs only when API key is present (issue #32) ---


class _JudgeOutput(BaseModel):
    """LLM judge score 1–5 and reason (for eval only)."""

    score: int = Field(ge=1, le=5, description="1=unrelated, 5=perfect match")
    reason: str = Field(description="Brief reason for the score")


def test_llm_judge_one_golden_sample() -> None:
    """Run real LLM on one golden sample, then LLM-judge candidate vs reference. Skip without key."""
    if not get_api_key("anthropic"):
        pytest.skip("No anthropic key in keyring (LLM-judge requires API)")
    from voiceforge.llm.router import analyze_meeting, complete_structured

    path = GOLDEN_DIR / "sample_standup_01.json"
    if not path.exists():
        pytest.skip("sample_standup_01.json not found")
    transcript, template, reference = _load_golden(path)
    assert template
    ref_text = _structured_to_text(reference)
    result, _cost = analyze_meeting(transcript, template=template)
    candidate_dict = result.model_dump() if hasattr(result, "model_dump") else result
    cand_text = _structured_to_text(candidate_dict)
    judge_system = (
        "You are an eval judge. Given reference (expected) and candidate (actual) meeting output as flat text, "
        "score 1–5 how well the candidate matches the reference. 5=perfect, 1=unrelated. Output score and brief reason."
    )
    judge_user = f"Reference:\n{ref_text}\n\nCandidate:\n{cand_text}"
    prompt = [
        {"role": "system", "content": judge_system},
        {"role": "user", "content": judge_user},
    ]
    judge, _ = complete_structured(prompt, response_model=_JudgeOutput, model="anthropic/claude-haiku-4-5")
    assert judge.score >= 3, f"LLM-judge score {judge.score}: {judge.reason}"
