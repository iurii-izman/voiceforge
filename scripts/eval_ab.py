#!/usr/bin/env python3
"""Phase D #70: A/B eval — run golden sample(s) with two models, compare ROUGE-L vs reference.

Usage:
  MODEL_A=anthropic/claude-haiku-4-5 MODEL_B=anthropic/claude-sonnet-4-6 uv run python scripts/eval_ab.py
  make eval-ab MODEL_A=haiku MODEL_B=sonnet   # uses defaults above
Skips if no API key. Light run: one golden sample only.
"""

from __future__ import annotations

import json
import os
import sys
from pathlib import Path

# Add project root
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from voiceforge.core.secrets import get_api_key


def _model_id(short: str) -> str:
    mapping = {
        "haiku": "anthropic/claude-haiku-4-5",
        "sonnet": "anthropic/claude-sonnet-4-6",
        "opus": "anthropic/claude-opus-4-6",
    }
    return mapping.get(short.lower(), short)


def _structured_to_text(obj: dict) -> str:
    parts = []
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


def _rouge_l(reference: str, candidate: str) -> float:
    if not reference.strip() and not candidate.strip():
        return 1.0
    if not reference.strip() or not candidate.strip():
        return 0.0
    from rouge_score import rouge_scorer

    scorer = rouge_scorer.RougeScorer(["rougeL"], use_stemmer=False)
    return scorer.score(reference, candidate)["rougeL"].fmeasure


def main() -> int:
    if not get_api_key("anthropic"):
        print("No anthropic key in keyring; skip A/B eval.", file=sys.stderr)
        return 0
    model_a = _model_id(os.environ.get("MODEL_A", "haiku"))
    model_b = _model_id(os.environ.get("MODEL_B", "sonnet"))

    base = Path(__file__).resolve().parent.parent
    golden_dir = base / "tests" / "eval" / "golden_samples"
    sample = golden_dir / "sample_standup_01.json"
    if not sample.exists():
        print(f"No {sample}; cannot run A/B.", file=sys.stderr)
        return 1
    data = json.loads(sample.read_text())
    transcript = data.get("transcript", "")
    template = data.get("template", "standup")
    reference = data.get("reference", {})
    ref_text = _structured_to_text(reference)

    from voiceforge.llm.router import analyze_meeting

    print(f"Running A/B: MODEL_A={model_a} vs MODEL_B={model_b} (1 golden sample)")
    result_a, _ = analyze_meeting(transcript, template=template, model=model_a)
    text_a = _structured_to_text(result_a.model_dump() if hasattr(result_a, "model_dump") else result_a)
    result_b, _ = analyze_meeting(transcript, template=template, model=model_b)
    text_b = _structured_to_text(result_b.model_dump() if hasattr(result_b, "model_dump") else result_b)

    rouge_a = _rouge_l(ref_text, text_a)
    rouge_b = _rouge_l(ref_text, text_b)
    print(f"ROUGE-L A: {rouge_a:.4f}")
    print(f"ROUGE-L B: {rouge_b:.4f}")
    print(f"Delta (B - A): {rouge_b - rouge_a:+.4f}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
