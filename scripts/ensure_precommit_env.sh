#!/usr/bin/env bash
# Ensure Python 3.12 for pre-commit (avoids 3.14.2 vs 3.14.3 cache mismatch).
# Fedora Atomic Cosmic: run inside toolbox; script installs python3.12 via dnf if missing.
set -euo pipefail

need_install=
if ! command -v python3.12 >/dev/null 2>&1; then
  if command -v dnf >/dev/null 2>&1; then
    echo "python3.12 not found; installing via dnf (Fedora/toolbox)..."
    sudo dnf install -y python3.12
    need_install=1
  elif command -v rpm-ostree >/dev/null 2>&1; then
    echo "python3.12 not found. On Atomic host run: rpm-ostree install python3.12 (then reboot if needed)."
    echo "Or run this script inside toolbox (recommended)."
    exit 1
  else
    echo "python3.12 not found and no dnf/rpm-ostree. Install Python 3.12 manually or use --no-verify for git."
    exit 1
  fi
fi

cd "${BASH_SOURCE[0]%/*}/.."
[ -n "${need_install:-}" ] && echo "Cleaning pre-commit cache..."
uv run pre-commit clean || true
echo "Installing pre-commit hooks..."
uv run pre-commit install --hook-type pre-commit --hook-type pre-push
echo "Done. Pre-commit will use python3.12 for hook environments."
