#!/usr/bin/env bash
set -euo pipefail

run_gitleaks() {
  if command -v gitleaks >/dev/null 2>&1; then
    gitleaks detect --source . --config .gitleaks.toml --no-git
    return 0
  fi
  if command -v podman >/dev/null 2>&1; then
    podman run --rm -v "$PWD:/repo:Z" -w /repo ghcr.io/gitleaks/gitleaks:latest \
      detect --source . --config .gitleaks.toml --no-git
    return 0
  fi
  if command -v docker >/dev/null 2>&1; then
    docker run --rm -v "$PWD:/repo" -w /repo ghcr.io/gitleaks/gitleaks:latest \
      detect --source . --config .gitleaks.toml --no-git
    return 0
  fi
  echo "gitleaks is not installed and no podman/docker runtime found" >&2
  return 1
}

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
run_gitleaks

echo "verify_pr.sh: ALL CHECKS PASSED"
