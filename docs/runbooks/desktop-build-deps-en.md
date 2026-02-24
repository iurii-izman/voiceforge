# Desktop (Tauri) build dependencies (EN)

For building the VoiceForge desktop app on **Fedora** (including Fedora Atomic Cosmic). Develop inside **toolbox** or distrobox; install the packages below there.

## System packages (Fedora)

To build inside toolbox or on the host:

```bash
sudo dnf install -y \
  gcc \
  nodejs \
  npm \
  pkg-config \
  webkit2gtk4.1-devel \
  gtk3-devel \
  openssl-devel
```

Or run the script from the repo root (inside toolbox): `./scripts/setup-desktop-toolbox.sh`

Optional (for system tray later):

```bash
sudo dnf install -y libappindicator-gtk3-devel
```

## Rust

Install Rust via rustup (inside toolbox):

```bash
curl --proto '=https' --tlsv1.2 -sSf https://sh.rustup.rs | sh
# then: source "$HOME/.cargo/env"
```

Or ensure `cargo` and `rustc` are available.

## Verify environment

From repo root:

```bash
./scripts/check-desktop-deps.sh
```

Or from `desktop/`:

```bash
cd desktop && cargo tauri build
```

If the script reports all checks OK, `cargo tauri build` should succeed. For OOM or crashes in the Python/daemon part (e.g. diarization), see [pyannote-version.md](pyannote-version.md).

## Full sequence in toolbox (reproducible build)

On Fedora Atomic (or when webkit/gtk are not installed on the host), build the desktop app only inside toolbox.

**One-time setup (in toolbox):**

```bash
toolbox enter
cd /path/to/voiceforge
./scripts/setup-desktop-toolbox.sh
```

The script installs: system packages (gcc, nodejs, npm, pkg-config, webkit2gtk4.1-devel, gtk3-devel, openssl-devel), Rust (rustup), tauri-cli, dependencies in `desktop/` (npm install), and finally runs `check-desktop-deps.sh`.

**Build:**

```bash
cd /path/to/voiceforge/desktop && npm run build && cargo tauri build
```

Artifacts: `desktop/src-tauri/target/release/bundle/`.

**Step by step (if not using the single script):**

1. **Enter toolbox:** `toolbox enter` (or `toolbox enter NAME`).
2. **Install dependencies:** packages from the section above (dnf) or `./scripts/setup-desktop-toolbox.sh` from repo root.
3. **Verify environment:** `./scripts/check-desktop-deps.sh` — all checks [OK].
4. **Build:** `cd desktop && npm run build && cargo tauri build`.

Without webkit2gtk-4.1 and gtk+-3.0, `check-desktop-deps` will report [FAIL]; in that case install the packages in toolbox (step 2).

## Common build errors (Rust)

- **`expected Result<MatchRule<'static>, zbus::Error>, found MatchRule<'_>`** in `desktop/src-tauri/src/dbus_signals.rs`: functions `rule_listen_state()` and `rule_analysis_done()` must return `Result` — wrap the return value in `Ok(...)` (`.build()` → `Ok(...build())`).
- **`no method named emit found for struct AppHandle<R>`**: in the same file the `Emitter` trait is required — add `use tauri::Emitter;` (or `use tauri::{AppHandle, Emitter};`).

## Release build and packaging

- Release binary: `cd desktop && npm run build && cargo tauri build`. Artifacts in `desktop/src-tauri/target/release/bundle/` (format depends on platform).
- Flatpak / AppImage: Tauri 2 supports both; Flatpak manifest can be added under `desktop/flatpak/` if needed. For alpha2, the binary from `cargo tauri build` is sufficient.

## Install and run after build

The daemon must be running before starting the desktop app (`uv run voiceforge daemon` in the same environment — host or toolbox).

**Run without installing (from repo):**

```bash
desktop/src-tauri/target/release/voiceforge-desktop
```

Or from `desktop/`: `./src-tauri/target/release/voiceforge-desktop`.

**Install via package (Fedora/RHEL):**

```bash
sudo dnf install desktop/src-tauri/target/release/bundle/rpm/VoiceForge-0.2.0-alpha.1-1.x86_64.rpm
```

After install the app is available from the menu or via `voiceforge-desktop` (or “VoiceForge”, depending on .desktop).

**Install via package (Debian/Ubuntu):**

```bash
sudo dpkg -i desktop/src-tauri/target/release/bundle/deb/VoiceForge_0.2.0-alpha.1_amd64.deb
```

Adjust the version in paths if you built a different one.

## COSMIC

No COSMIC-specific APIs are required. Standard D-Bus session and Wayland/X11 are enough. Custom shortcuts (e.g. for Analyze) are configured in COSMIC Settings → Keyboard → Custom Shortcuts (dbus-send to `com.voiceforge.App`).
