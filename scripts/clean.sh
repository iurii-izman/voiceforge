#!/usr/bin/env bash
set -euo pipefail

mode="safe"
if [[ "${1:-}" == "--deep" ]]; then
  mode="deep"
elif [[ "${1:-}" == "--safe" || -z "${1:-}" ]]; then
  mode="safe"
else
  echo "Usage: $0 [--safe|--deep]" >&2
  exit 1
fi

rm -rf \
  .pytest_cache \
  .ruff_cache \
  .mypy_cache \
  .uv-cache \
  htmlcov \
  dist \
  reports \
  tests/**/__pycache__ \
  src/**/__pycache__

find . -type d -name __pycache__ -prune -exec rm -rf {} + 2>/dev/null || true
find . -type f -name '*.pyc' -delete 2>/dev/null || true

if [[ "$mode" == "deep" ]]; then
  rm -rf .venv
fi

echo "clean complete ($mode)"
