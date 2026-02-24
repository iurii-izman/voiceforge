#!/usr/bin/env bash
# Prepare toolbox (or Fedora host) for building the VoiceForge desktop app.
# Run from repo root: ./scripts/setup-desktop-toolbox.sh
# Or inside toolbox: cd /path/to/voiceforge && ./scripts/setup-desktop-toolbox.sh
set -euo pipefail

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$REPO_ROOT"

echo "=== VoiceForge desktop: setup (repo $REPO_ROOT) ==="

# 1. System packages (Fedora)
if command -v dnf >/dev/null 2>&1; then
  echo "--- Installing system packages (gcc, webkit, gtk, openssl)..."
  sudo dnf install -y \
    gcc \
    nodejs \
    npm \
    webkit2gtk4.1-devel \
    gtk3-devel \
    openssl-devel \
    pkg-config \
    librsvg2-devel
else
  echo "[WARN] dnf not found; skip system packages (install manually on Fedora)"
fi

# 2. Rust
if ! command -v cargo >/dev/null 2>&1; then
  echo "--- Installing Rust (rustup)..."
  curl --proto '=https' --tlsv1.2 -sSf https://sh.rustup.rs | sh -s -- -y
  # shellcheck source=/dev/null
  source "$HOME/.cargo/env"
else
  echo "[OK] Rust already present: $(cargo --version)"
  source "$HOME/.cargo/env" 2>/dev/null || true
fi

# 3. Tauri CLI
if ! cargo tauri --version >/dev/null 2>&1; then
  echo "--- Installing tauri-cli..."
  cargo install tauri-cli
else
  echo "[OK] tauri-cli: $(cargo tauri --version 2>&1 | head -1)"
fi

# 4. Node deps in desktop/
if [[ -d "$REPO_ROOT/desktop" ]]; then
  echo "--- npm install in desktop/..."
  (cd "$REPO_ROOT/desktop" && npm install)
else
  echo "[FAIL] desktop/ not found"
  exit 1
fi

# 5. Verify
echo "--- Verifying environment..."
"$REPO_ROOT/scripts/check-desktop-deps.sh"

echo "=== Setup done. Build with: cd desktop && npm run build && cargo tauri build ==="
