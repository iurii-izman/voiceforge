#!/usr/bin/env bash
# Install linuxdeploy + appimage plugin for building Tauri AppImage (e.g. inside toolbox).
# Run inside toolbox: ./scripts/install_linuxdeploy_toolbox.sh
# See: https://github.com/linuxdeploy/linuxdeploy , desktop-build-deps.md
set -euo pipefail

BIN_DIR="${HOME}/.local/bin"
mkdir -p "$BIN_DIR"

LINUXDEPLOY_URL="https://github.com/linuxdeploy/linuxdeploy/releases/download/continuous/linuxdeploy-x86_64.AppImage"
PLUGIN_APPIMAGE_URL="https://github.com/linuxdeploy/linuxdeploy-plugin-appimage/releases/download/continuous/linuxdeploy-plugin-appimage-x86_64.AppImage"

echo "Installing linuxdeploy to $BIN_DIR ..."
curl -sL -o "$BIN_DIR/linuxdeploy-x86_64.AppImage" "$LINUXDEPLOY_URL"
chmod +x "$BIN_DIR/linuxdeploy-x86_64.AppImage"

echo "Installing linuxdeploy-plugin-appimage ..."
curl -sL -o "$BIN_DIR/linuxdeploy-plugin-appimage-x86_64.AppImage" "$PLUGIN_APPIMAGE_URL"
chmod +x "$BIN_DIR/linuxdeploy-plugin-appimage-x86_64.AppImage"

# Tauri looks for 'linuxdeploy' in PATH; many images expect the binary without -x86_64
if [[ ! -x "$BIN_DIR/linuxdeploy" ]]; then
  ln -sf linuxdeploy-x86_64.AppImage "$BIN_DIR/linuxdeploy"
fi

echo "Done. Ensure $BIN_DIR is in your PATH (e.g. export PATH=\"$BIN_DIR:\$PATH\")."
echo ""
echo "To build AppImage (from repo root):"
echo "  export PATH=\"$BIN_DIR:\$PATH\""
echo "  export NO_STRIP=true"
echo "  export APPIMAGE_EXTRACT_AND_RUN=1   # required in toolbox (no FUSE)"
echo "  cd desktop && npm run build && npm run tauri build"
echo ""
if [[ ":$PATH:" != *":$BIN_DIR:"* ]]; then
  echo "Add to ~/.bashrc: export PATH=\"$BIN_DIR:\$PATH\""
fi
