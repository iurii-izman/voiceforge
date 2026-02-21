#!/usr/bin/env bash
set -euo pipefail

echo "[1/5] Ruff"
uv run ruff check src tests scripts

echo "[2/5] Mypy"
uv run mypy src/voiceforge/core src/voiceforge/llm src/voiceforge/rag src/voiceforge/stt --ignore-missing-imports

echo "[3/5] Tests"
uv run pytest tests -q

echo "[4/5] Security"
uv run pip-audit --desc --ignore-vuln CVE-2025-69872
uv run bandit -r src -ll -q --configfile .bandit.yaml

echo "[5/5] Gitleaks"
gitleaks detect --source . --config .gitleaks.toml

echo "verify_pr.sh: ALL CHECKS PASSED"
