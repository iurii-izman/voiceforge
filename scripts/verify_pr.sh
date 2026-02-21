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

echo "[1/8] Toolchain"
./scripts/check_toolchain.sh

echo "[2/8] Ruff"
uv run ruff check src tests scripts

echo "[3/8] Mypy"
uv run mypy src/voiceforge/core src/voiceforge/llm src/voiceforge/rag src/voiceforge/stt --ignore-missing-imports

echo "[4/8] Tests + Coverage"
uv run pytest tests -q --cov=src/voiceforge --cov-report=xml --cov-report=json --cov-fail-under=0

echo "[5/8] New-code coverage"
./scripts/check_new_code_coverage.sh

echo "[6/8] CLI contract"
./scripts/check_cli_contract.sh

echo "[7/8] Security"
uv run pip-audit --desc --ignore-vuln CVE-2025-69872
uv run bandit -r src -ll -q --configfile .bandit.yaml

echo "[8/8] Gitleaks"
run_gitleaks

echo "verify_pr.sh: ALL CHECKS PASSED"
