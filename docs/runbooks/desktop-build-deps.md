# Desktop (Tauri) build dependencies

For building the VoiceForge desktop app on **Fedora** (including Fedora Atomic Cosmic). Develop inside **toolbox** or distrobox; install the packages below there.

## Системные пакеты (Fedora)

Для сборки в toolbox или на хосте:

```bash
sudo dnf install -y \
  gcc \
  nodejs \
  npm \
  webkit2gtk4.1-devel \
  gtk3-devel \
  openssl-devel
```

Либо один скрипт из корня репо (внутри toolbox): `./scripts/setup-desktop-toolbox.sh`

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

## Полная последовательность в toolbox

На Fedora Atomic (или без webkit/gtk на хосте) сборка десктопа только внутри toolbox:

1. **Войти в toolbox:** `toolbox enter` (или `toolbox enter ИМЯ`).
2. **Установить зависимости:** пакеты из раздела выше (dnf) или один скрипт:
   ```bash
   cd /path/to/voiceforge
   ./scripts/setup-desktop-toolbox.sh
   ```
3. **Проверить окружение:** `./scripts/check-desktop-deps.sh` — все проверки должны быть [OK].
4. **Собрать:** `cd desktop && npm run build && cargo tauri build`. Артефакты в `desktop/src-tauri/target/release/bundle/`.

Без webkit2gtk-4.1 и gtk+-3.0 `check-desktop-deps` выдаст [FAIL]; в этом случае устанавливать пакеты в toolbox (шаг 2).

## Сборка релиза и упаковка

- Релизный бинарник: `cd desktop && npm run build && cargo tauri build`. Артефакты в `desktop/src-tauri/target/release/bundle/` (формат зависит от платформы).
- Flatpak / AppImage: Tauri 2 поддерживает оба; манифест Flatpak при необходимости добавляется в `desktop/flatpak/`. Для альфа2 достаточно бинарника из `cargo tauri build`.

## COSMIC

No COSMIC-specific APIs are required. Standard D-Bus session and Wayland/X11 are enough. Custom shortcuts (e.g. for Analyze) are configured in COSMIC Settings → Keyboard → Custom Shortcuts (dbus-send to `com.voiceforge.App`).
