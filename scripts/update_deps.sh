#!/usr/bin/env bash
set -euo pipefail

if ! command -v uv >/dev/null 2>&1; then
  echo "uv is required" >&2
  exit 1
fi

echo "Updating lockfile..."
uv lock --upgrade

echo "Syncing and validating..."
uv sync --extra all
./scripts/verify_pr.sh

echo "update_deps.sh: dependency update is valid"
