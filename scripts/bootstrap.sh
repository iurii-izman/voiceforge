#!/usr/bin/env bash
# E8 (#131): bootstrap with optional model download, PipeWire check, RAM warning, final hint
set -euo pipefail

echo "VoiceForge bootstrap (alpha2 line)"

if ! command -v uv >/dev/null 2>&1; then
  echo "uv is required. Install uv first." >&2
  exit 1
fi

# PipeWire check (E1/E3)
if ! command -v pw-record >/dev/null 2>&1; then
  echo "⚠ PipeWire not found. Install: sudo dnf install pipewire pipewire-utils" >&2
fi
if command -v pipewire >/dev/null 2>&1; then
  pipewire --version 2>/dev/null || true
fi

uv sync --extra all

# E8: optional model pre-download (skip with --skip-models)
SKIP_MODELS=false
for arg in "$@"; do
  if [ "$arg" = "--skip-models" ]; then
    SKIP_MODELS=true
    break
  fi
done
if [ "$SKIP_MODELS" = false ]; then
  echo "Pre-downloading models (Whisper + ONNX check)..."
  uv run voiceforge download-models --no-progress || true
fi

# RAM check: warn if <4GB available (E8)
if command -v python3 >/dev/null 2>&1; then
  AVAIL_GB=$(python3 -c "
import sys
try:
  import psutil
  gb = psutil.virtual_memory().available / (1024**3)
  print(f'{gb:.1f}')
except Exception:
  print('?')
" 2>/dev/null || echo "?")
  if [ "$AVAIL_GB" != "?" ] && [ -n "$AVAIL_GB" ]; then
    # shellcheck disable=SC2086
    if awk "BEGIN { exit !($AVAIL_GB < 4) }" 2>/dev/null; then
      echo "⚠ Low RAM: ${AVAIL_GB} GB available (recommended ≥4 GB for full pipeline)" >&2
    fi
  fi
fi

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

echo "Setup complete! Run: voiceforge meeting"
