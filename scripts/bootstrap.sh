#!/usr/bin/env bash
set -euo pipefail

echo "VoiceForge alpha0.1 bootstrap"

if ! command -v uv >/dev/null 2>&1; then
  echo "uv is required. Install uv first." >&2
  exit 1
fi

uv sync --extra all

echo "Set keyring entries if missing:"
echo "  keyring set voiceforge anthropic"
echo "  keyring set voiceforge openai"
echo "  keyring set voiceforge huggingface"

echo "Smoke check:"
uv run voiceforge status || true

echo "Done. Start capture: uv run voiceforge listen"
