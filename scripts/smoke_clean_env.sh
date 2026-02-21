#!/usr/bin/env bash
set -euo pipefail

tmp="$(mktemp -d -p "${PWD}" .tmp-smoke.XXXXXX)"
cleanup() {
  rm -rf "$tmp"
  return 0
}
trap cleanup EXIT

echo "Smoke sandbox: $tmp"

mkdir -p "$tmp/repo"
if command -v rsync >/dev/null 2>&1; then
  rsync -a --delete \
    --exclude ".git" \
    --exclude ".venv" \
    --exclude ".mypy_cache" \
    --exclude ".pytest_cache" \
    --exclude ".ruff_cache" \
    --exclude "__pycache__" \
    ./ "$tmp/repo/"
else
  tar \
    --exclude ".git" \
    --exclude ".venv" \
    --exclude ".mypy_cache" \
    --exclude ".pytest_cache" \
    --exclude ".ruff_cache" \
    --exclude "__pycache__" \
    -cf - . | tar -xf - -C "$tmp/repo"
fi

cd "$tmp/repo"

if ! command -v uv >/dev/null 2>&1; then
  echo "uv is required for smoke run" >&2
  exit 1
fi

uv sync --extra all

uv run voiceforge --help >/dev/null
uv run voiceforge status >/dev/null
uv run voiceforge listen --help >/dev/null
uv run voiceforge analyze --help >/dev/null
uv run voiceforge history --help >/dev/null
uv run voiceforge index --help >/dev/null
uv run voiceforge watch --help >/dev/null
uv run voiceforge daemon --help >/dev/null

if uv run voiceforge tasks >/dev/null 2>&1; then
  echo "Expected removed command 'tasks' to fail" >&2
  exit 1
fi

echo "smoke_clean_env.sh: OK"
