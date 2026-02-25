#!/usr/bin/env bash
# Build VoiceForge desktop Flatpak from a locally built .deb.
# Run from repo root. Requires: flatpak, flatpak-builder, org.gnome.Platform//46.
# If .deb is missing, builds desktop first (needs Node, Rust, deps — see desktop-build-deps.md).
set -euo pipefail

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$REPO_ROOT"
MANIFEST="$REPO_ROOT/desktop/flatpak/com.voiceforge.app.yaml"
BUNDLE_DEB_DIR="$REPO_ROOT/desktop/src-tauri/target/release/bundle/deb"

if ! command -v flatpak-builder >/dev/null 2>&1; then
  echo "ERROR: flatpak-builder not found. Install: sudo dnf install flatpak-builder && flatpak install flathub org.gnome.Platform//46 org.gnome.Sdk//46"
  exit 1
fi

# Build .deb if missing
if ! compgen -G "$BUNDLE_DEB_DIR/VoiceForge_"*"_amd64.deb" >/dev/null 2>&1; then
  echo "=== .deb not found; building desktop (npm run build && cargo tauri build) ==="
  cd "$REPO_ROOT/desktop"
  npm run build
  cargo tauri build
  cd "$REPO_ROOT"
fi

DEB=$(echo "$BUNDLE_DEB_DIR"/VoiceForge_*_amd64.deb)
if [[ ! -f "$DEB" ]]; then
  echo "ERROR: No .deb at $BUNDLE_DEB_DIR/VoiceForge_*_amd64.deb"
  exit 1
fi
DEB_ABS=$(readlink -f "$DEB")
SHA256=$(sha256sum "$DEB" | awk '{print $1}')
echo "=== Using .deb: $DEB_ABS (sha256: $SHA256) ==="

# Patched manifest for local build (file:// + sha256); not committed
LOCAL_MF="$REPO_ROOT/desktop/flatpak/com.voiceforge.app.local.yaml"
sed -e "s|url: .*|url: file://$DEB_ABS|" -e "s|sha256: .*|sha256: $SHA256|" "$MANIFEST" > "$LOCAL_MF"

echo "=== Running flatpak-builder ==="
flatpak-builder --user --force-clean build "$LOCAL_MF"
echo "=== Done. Run once: flatpak-builder --run build desktop/flatpak/com.voiceforge.app.local.yaml com.voiceforge.app"
echo "  Or install: flatpak-builder --user --install build desktop/flatpak/com.voiceforge.app.local.yaml && flatpak run com.voiceforge.app"
