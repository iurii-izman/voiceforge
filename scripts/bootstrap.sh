#!/usr/bin/env bash
set -euo pipefail

echo "VoiceForge bootstrap (alpha2 line)"

if ! command -v uv >/dev/null 2>&1; then
  echo "uv is required. Install uv first." >&2
  exit 1
fi

if ! command -v pw-record >/dev/null 2>&1; then
  echo "⚠ PipeWire not found. Install: sudo dnf install pipewire pipewire-utils" >&2
fi
if command -v pipewire >/dev/null 2>&1; then
  pipewire --version 2>/dev/null || true
fi

uv sync --extra all

echo "Ensuring pre-commit env (python3.12 + hooks)..."
./scripts/ensure_precommit_env.sh

echo "Set keyring entries if missing:"
echo "  keyring set voiceforge anthropic"
echo "  keyring set voiceforge openai"
echo "  keyring set voiceforge huggingface"

echo "Doctor check:"
./scripts/doctor.sh || true

echo "Smoke check:"
uv run voiceforge status || true

echo "Done. Start capture: uv run voiceforge listen"
