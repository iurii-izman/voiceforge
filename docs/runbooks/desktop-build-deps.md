# Desktop (Tauri) build dependencies

For building the VoiceForge desktop app on **Fedora** (including Fedora Atomic Cosmic). Develop inside **toolbox** or distrobox; install the packages below there.

## System packages (Fedora)

```bash
sudo dnf install -y \
  webkit2gtk4.1-devel \
  gtk3-devel \
  openssl-devel
```

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

If the script reports all checks OK, `cargo tauri build` should succeed.

## Сборка релиза и упаковка

- Релизный бинарник: `cd desktop && npm run build && cargo tauri build`. Артефакты в `desktop/src-tauri/target/release/bundle/` (формат зависит от платформы).
- Flatpak / AppImage: Tauri 2 поддерживает оба; манифест Flatpak при необходимости добавляется в `desktop/flatpak/`. Для альфа2 достаточно бинарника из `cargo tauri build`.

## COSMIC

No COSMIC-specific APIs are required. Standard D-Bus session and Wayland/X11 are enough. Custom shortcuts (e.g. for Analyze) are configured in COSMIC Settings → Keyboard → Custom Shortcuts (dbus-send to `com.voiceforge.App`).
