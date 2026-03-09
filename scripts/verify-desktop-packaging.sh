#!/usr/bin/env bash
# E19 #142: Desktop packaging verification — build Tauri and assert bundle artifacts exist.
# Run from repo root. Requires: Node, npm, Rust, desktop deps (see desktop-build-deps.md).
# Optional: flatpak-builder for Flatpak verification (./scripts/build-flatpak.sh).
set -euo pipefail

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$REPO_ROOT"
BUNDLE_BASE="$REPO_ROOT/desktop/src-tauri/target/release/bundle"

echo "=== Desktop packaging verification (E19 #142) ==="

# Build desktop if bundle dir missing or empty
if [[ ! -d "$BUNDLE_BASE" ]] || ! compgen -G "$BUNDLE_BASE/deb/"*.deb >/dev/null 2>&1; then
  echo "=== Building desktop (npm run build && npm run tauri build) ==="
  cd "$REPO_ROOT/desktop"
  npm run build
  npm run tauri build
  cd "$REPO_ROOT"
fi

OK=0

# Deb
if compgen -G "$BUNDLE_BASE/deb/"*.deb >/dev/null 2>&1; then
  DEB=$(echo "$BUNDLE_BASE/deb/"*.deb)
  echo "OK  .deb: $DEB"
  OK=$((OK + 1))
else
  echo "MISSING  .deb under $BUNDLE_BASE/deb/"
fi

# AppImage
if compgen -G "$BUNDLE_BASE/appimage/"*.AppImage >/dev/null 2>&1; then
  APPIMG=$(echo "$BUNDLE_BASE/appimage/"*.AppImage)
  echo "OK  AppImage: $APPIMG"
  OK=$((OK + 1))
else
  echo "MISSING  .AppImage under $BUNDLE_BASE/appimage/"
fi

echo "=== Verification: $OK bundle(s) OK ==="
if [[ $OK -lt 1 ]]; then
  echo "ERROR: At least one of deb/AppImage must be present. See docs/runbooks/offline-package.md" >&2
  exit 1
fi
echo "Flatpak: run ./scripts/build-flatpak.sh from repo root (see docs/runbooks/offline-package.md)."
exit 0
