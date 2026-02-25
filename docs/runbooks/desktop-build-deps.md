# Desktop (Tauri) build dependencies

For building the VoiceForge desktop app on **Fedora** (including Fedora Atomic Cosmic). Develop inside **toolbox** or distrobox; install the packages below there.

## Системные пакеты (Fedora)

Для сборки в toolbox или на хосте:

```bash
sudo dnf install -y \
  gcc \
  nodejs \
  npm \
  pkg-config \
  webkit2gtk4.1-devel \
  gtk3-devel \
  openssl-devel \
  librsvg2-devel
```

`librsvg2-devel` is required for AppImage bundling (linuxdeploy gtk plugin).

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

If the script reports all checks OK, `cargo tauri build` should succeed. For OOM or crashes in the Python/daemon part (e.g. diarization), see [pyannote-version.md](pyannote-version.md).

## Полная последовательность в toolbox (воспроизводимая сборка)

На Fedora Atomic (или без webkit/gtk на хосте) сборка десктопа только внутри toolbox.

**Однократная подготовка (в toolbox):**

```bash
toolbox enter
cd /path/to/voiceforge
./scripts/setup-desktop-toolbox.sh
```

Скрипт устанавливает: системные пакеты (gcc, nodejs, npm, pkg-config, webkit2gtk4.1-devel, gtk3-devel, openssl-devel), Rust (rustup), tauri-cli, зависимости в `desktop/` (npm install) и в конце запускает `check-desktop-deps.sh`.

**Сборка:**

```bash
cd /path/to/voiceforge/desktop && npm run build && cargo tauri build
```

Артефакты: `desktop/src-tauri/target/release/bundle/`.

**По шагам (если не используете один скрипт):**

1. **Войти в toolbox:** `toolbox enter` (или `toolbox enter ИМЯ`).
2. **Установить зависимости:** пакеты из раздела выше (dnf) или `./scripts/setup-desktop-toolbox.sh` из корня репо.
3. **Проверить окружение:** `./scripts/check-desktop-deps.sh` — все проверки [OK].
4. **Собрать:** `cd desktop && npm run build && cargo tauri build`.

Без webkit2gtk-4.1 и gtk+-3.0 `check-desktop-deps` выдаст [FAIL]; в этом случае устанавливать пакеты в toolbox (шаг 2).

## Частые ошибки сборки (Rust)

- **`expected Result<MatchRule<'static>, zbus::Error>, found MatchRule<'_>`** в `desktop/src-tauri/src/dbus_signals.rs`: функции `rule_listen_state()` и `rule_analysis_done()` должны возвращать `Result` — обернуть возвращаемое значение в `Ok(...)` (`.build()` → `Ok(...build())`).
- **`no method named emit found for struct AppHandle<R>`**: в том же файле нужен трейт `Emitter` — добавить `use tauri::Emitter;` (или `use tauri::{AppHandle, Emitter};`).

## Сборка релиза и упаковка

- Релизный бинарник: `cd desktop && npm run build && cargo tauri build`. Артефакты в `desktop/src-tauri/target/release/bundle/` (deb, rpm, appimage).
- **Flatpak:** манифест `desktop/flatpak/com.voiceforge.app.yaml`. Локальная сборка из .deb: `./scripts/build-flatpak.sh` (см. `offline-package.md`). Требуются flatpak-builder и runtime org.gnome.Platform//46.

### AppImage в toolbox (Fedora)

На Fedora/rolling distros для успешной сборки AppImage нужны переменные окружения (из‑за linuxdeploy и секций `.relr.dyn`):

```bash
export NO_STRIP=true
export APPIMAGE_EXTRACT_AND_RUN=1
cd desktop && npm run build && cargo tauri build
```

Убедитесь, что установлен `librsvg2-devel` (см. системные пакеты выше). Артефакт: `desktop/src-tauri/target/release/bundle/appimage/VoiceForge_*_amd64.AppImage`.

## Установка и запуск после сборки

Перед запуском десктопа должен быть запущен демон (`uv run voiceforge daemon` в том же окружении — хосте или toolbox).

**Запуск без установки (из каталога репо):**

```bash
desktop/src-tauri/target/release/voiceforge-desktop
```

Или из `desktop/`: `./src-tauri/target/release/voiceforge-desktop`.

**Установка пакетом (Fedora/RHEL):**

```bash
sudo dnf install desktop/src-tauri/target/release/bundle/rpm/VoiceForge-0.2.0-alpha.1-1.x86_64.rpm
```

После установки приложение доступно в меню или по команде `voiceforge-desktop` (или «VoiceForge», в зависимости от .desktop).

**Установка пакетом (Debian/Ubuntu):**

```bash
sudo dpkg -i desktop/src-tauri/target/release/bundle/deb/VoiceForge_0.2.0-alpha.1_amd64.deb
```

Версию в путях подставьте свою, если собирали другую.

## COSMIC

No COSMIC-specific APIs are required. Standard D-Bus session and Wayland/X11 are enough. Custom shortcuts (e.g. for Analyze) are configured in COSMIC Settings → Keyboard → Custom Shortcuts (dbus-send to `com.voiceforge.App`).
