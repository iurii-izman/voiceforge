#!/usr/bin/env bash
# Check that the environment is ready for building the Tauri desktop app (cargo tauri build).
# Run from repo root or from desktop/.
set -euo pipefail

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
DESKTOP_DIR="$REPO_ROOT/desktop"
errors=0
warnings=0

ok() { echo "[OK] $*"; return 0; }
warn() { echo "[WARN] $*"; ((warnings++)) || true; return 0; }
fail() { echo "[FAIL] $*"; ((errors++)) || true; return 1; }

# Cargo / Rust
if command -v cargo >/dev/null 2>&1; then
  ok "cargo: $(cargo --version)"
else
  fail "cargo not found (install rustup)"
fi

if command -v rustc >/dev/null 2>&1; then
  ok "rustc: $(rustc --version)"
else
  fail "rustc not found"
fi

# Tauri CLI (optional but recommended for tauri build)
if cargo tauri --version >/dev/null 2>&1; then
  ok "cargo tauri: $(cargo tauri --version 2>&1 | head -1)"
else
  warn "cargo tauri not installed (run: cargo install tauri-cli)"
fi

# Node.js / npm (for desktop: npm run build before cargo tauri build)
if command -v node >/dev/null 2>&1; then
  ok "node: $(node --version 2>/dev/null || echo '?')"
else
  fail "node not found (Fedora: dnf install nodejs)"
fi
if command -v npm >/dev/null 2>&1; then
  ok "npm: $(npm --version 2>/dev/null || echo '?')"
else
  fail "npm not found (Fedora: dnf install npm)"
fi

# Fedora: pkg-config and dev headers for WebKit/GTK
if command -v pkg-config >/dev/null 2>&1; then
  ok "pkg-config: $(pkg-config --version)"
  if pkg-config --exists webkit2gtk-4.1 2>/dev/null; then
    ok "webkit2gtk-4.1 (pkg-config)"
  else
    fail "webkit2gtk-4.1 not found (Fedora: dnf install webkit2gtk4.1-devel)"
  fi
  if pkg-config --exists gtk+-3.0 2>/dev/null; then
    ok "gtk+-3.0 (pkg-config)"
  else
    fail "gtk+-3.0 not found (Fedora: dnf install gtk3-devel)"
  fi
else
  warn "pkg-config not found; cannot check webkit/gtk"
fi

# desktop/ project (Tauri: Rust in src-tauri/)
if [[ -d "$DESKTOP_DIR" ]] && [[ -f "$DESKTOP_DIR/src-tauri/Cargo.toml" ]]; then
  ok "desktop/ project present"
else
  fail "desktop/ or desktop/src-tauri/Cargo.toml missing"
fi

if [[ $errors -gt 0 ]]; then
  echo "--- $errors check(s) failed. Fix them before running: cd desktop && cargo tauri build"
  exit 1
fi
if [[ $warnings -gt 0 ]]; then
  echo "--- $warnings warning(s). You may need: cargo install tauri-cli"
fi
echo "--- Desktop build deps OK"
