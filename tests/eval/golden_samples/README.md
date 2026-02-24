# Golden samples for LLM eval

Each file: JSON with `transcript`, `template` (optional: standup, sprint_review, one_on_one, brainstorm, interview), and `reference` (expected structured output as dict).

Used by `tests/eval/test_llm_eval.py` for ROUGE-L and regression checks.
Target: 20+ samples covering all 5 templates (issue #32).
