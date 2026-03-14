# Офлайн-пакет (Flatpak / AppImage) — roadmap 14, Phase D #73

Черновик для упаковки десктопного приложения VoiceForge (Tauri 2) в форматы, не требующие установки системных пакетов на целевой машине.

## Воспроизводимая сборка (repeatable path)

- **Версии:** синхронизация версий и контракт updater проверяются скриптом `scripts/check_release_metadata.py` (обязателен перед релизом, см. [release-and-quality.md](release-and-quality.md) § 1.1).
- **Проверка упаковки (E19 #142):** из корня репо `./scripts/verify-desktop-packaging.sh` — собирает десктоп при необходимости и проверяет наличие артефактов .deb и .AppImage в `desktop/src-tauri/target/release/bundle/`.
- **Flatpak из корня репо:** `make flatpak-build` или `./scripts/build-flatpak.sh`. Требует: flatpak, flatpak-builder, org.gnome.Platform//46; при отсутствии .deb скрипт сначала собирает десктоп (см. [desktop-build-deps.md](desktop-build-deps.md)).
- **Deb/RPM/AppImage:** из каталога `desktop/`: `npm run build && npm run tauri build` (зависимости и шаги — в [desktop-build-deps.md](desktop-build-deps.md)).
- **Updater:** до настройки ключей и сервера обновлений — явно отключён (`pubkey` и `endpoints` пустые в tauri.conf.json). См. [desktop-updater.md](desktop-updater.md) § 0.

## GA checklist (#73)

- **AppImage:** скачать `.AppImage` → `chmod +x VoiceForge_*.AppImage` → `./VoiceForge_*.AppImage` (приложение запускается).
- **Flatpak:** `flatpak install <источник> com.voiceforge.app` → `flatpak run com.voiceforge.app` (приложение запускается).
- **Сборка из дерева:** `make flatpak-build`; AppImage: см. раздел AppImage ниже и `desktop-build-deps.md`.

## Критерии приёмки GA (#73)

- **AppImage:** пользователь может скачать один файл `.AppImage` → `chmod +x VoiceForge_*.AppImage` → `./VoiceForge_*.AppImage` (приложение запускается; демон VoiceForge на хосте должен быть запущен отдельно).
- **Flatpak:** пользователь может выполнить `flatpak install <источник> com.voiceforge.app` (или установить из Flathub/локального репо) → `flatpak run com.voiceforge.app` (приложение запускается).
- **Сборка из дерева:** `make flatpak-build` (см. ниже) или по шагам в разделах AppImage/Flatpak.

## Зависимости и предпосылки

- **Сборка десктопа** уже воспроизводима в toolbox (см. `desktop-build-deps.md`): `./scripts/setup-desktop-toolbox.sh` → `cd desktop && npm run build && cargo tauri build`.
- Текущий `bundle.targets` в `desktop/src-tauri/tauri.conf.json`: `["deb", "rpm", "appimage"]`.
- **CLI и демон** VoiceForge — отдельно: пользователь устанавливает их по `installation-guide.md` (uv/pip); офлайн-пакет в альфа2 — только **десктопное приложение** (UI), которое общается с демоном по D-Bus.

## AppImage

- **Плюсы:** один файл, не требует установки, работает на многих дистрибутивах.
- **Ограничения:** собирать на старом glibc (или в Docker/CI), если нужна совместимость со старыми системами; размер ~70+ MB; ARM только на ARM-хосте.
- **Tauri 2:** поддерживается через bundle (см. [Tauri 2 AppImage](https://v2.tauri.app/distribute/appimage)).
- **Этапы (черновик):**
  1. Добавить в `tauri.conf.json` в `bundle.targets` цель `appimage` (или использовать `cargo tauri build --target appimage` при поддержке).
  2. Сборка в toolbox (Fedora): после успешной сборки deb/rpm проверить наличие цели appimage в Tauri 2.
  3. Для воспроизводимости и совместимости glibc — собирать в Docker (например, образ на базе Ubuntu 20.04/22.04) или в GitHub Actions.
  4. Подпись (опционально): см. [Tauri Linux Code Signing](https://v2.tauri.app/distribute/sign/linux).

## Flatpak

- **Плюсы:** распространение через Flathub, изоляция, единый runtime.
- **Ограничения:** нужен манифест, runtime (например GNOME), публикация на Flathub — отдельный процесс.
- **Tauri 2:** поддерживается через манифест (см. [Tauri 2 Flatpak](https://v2.tauri.app/distribute/flatpak/)).
- **Манифест:** `desktop/flatpak/com.voiceforge.app.yaml` (id: `com.voiceforge.app`). Sandbox: Wayland/X11, DRI, PulseAudio, D-Bus `com.voiceforge.App`, Secret Service `org.freedesktop.secrets`.

### Требования

- Flatpak и flatpak-builder: `sudo dnf install flatpak flatpak-builder` (в toolbox или на хосте).
- Runtime: `flatpak install flathub org.gnome.Platform//46 org.gnome.Sdk//46`.

### Сборка и тест (локально / в toolbox)

**Вариант A — из готового .deb (релизный URL):**
В манифесте указан URL на GitHub Releases и sha256. Для v1.0.0-beta.1 sha256 в манифесте уже подставлен (сборка из дерева). Если в Release ещё нет .deb — загрузите его из `desktop/src-tauri/target/release/bundle/deb/VoiceForge_1.0.0-beta.1_amd64.deb`, чтобы `flatpak-builder` мог скачать артефакт.

```bash
cd /path/to/voiceforge
flatpak-builder --user --force-clean build desktop/flatpak/com.voiceforge.app.yaml
flatpak-builder --run build desktop/flatpak/com.voiceforge.app.yaml com.voiceforge.app
```

**Вариант B — из локально собранного .deb:**
Сначала соберите десктоп (см. `desktop-build-deps.md`), затем подставьте в манифест локальный путь и sha256 или используйте скрипт:

```bash
cd /path/to/voiceforge
# 1) Собрать .deb (если ещё не собран)
cd desktop && npm run build && cargo tauri build && cd ..
DEB=$(echo desktop/src-tauri/target/release/bundle/deb/VoiceForge_*_amd64.deb)
# 2) Подставить в манифест url: file://$PWD/... и sha256 от $DEB, затем:
flatpak-builder --user --force-clean build desktop/flatpak/com.voiceforge.app.yaml
flatpak-builder --run build desktop/flatpak/com.voiceforge.app.yaml com.voiceforge.app
```

Удобно использовать скрипт `scripts/build-flatpak.sh` (если есть): он собирает .deb при необходимости и запускает flatpak-builder с подставленным file:// и sha256.

### Установка (опционально)

После **локальной** сборки через `./scripts/build-flatpak.sh` используется сгенерированный манифест `.local.yaml`:
```bash
flatpak-builder --user --install build desktop/flatpak/com.voiceforge.app.local.yaml
flatpak run com.voiceforge.app
```
Для установки из репозитория (без локальной сборки) — манифест `com.voiceforge.app.yaml` с подставленным sha256 релизного .deb.

Перед запуском приложения должен быть запущен демон VoiceForge (`uv run voiceforge daemon`) на сессии — Flatpak-приложение подключается к нему по D-Bus.

### Flathub submission

- Заменить в манифесте `PLACEHOLDER_REPLACE_WITH_ACTUAL_SHA256` на sha256 загруженного .deb.
- По желанию добавить AppStream metainfo (appdata) для карточки на Flathub.
- Следовать [Flathub submission guidelines](https://docs.flathub.org/docs/for-app-authors/).

## Рекомендация для альфа2

- Для альфа2 достаточно **бинарника из `cargo tauri build`** (deb/rpm или артефакты в `target/release/bundle/`); установка по `desktop-build-deps.md` и `installation-guide.md`.
- **Flatpak/AppImage** — после стабилизации ядра и десктопа: сначала выбрать один формат (например AppImage для простого раздачи одного файла или Flatpak для Flathub), затем описать полную последовательность в этом runbook и при необходимости скрипты в `scripts/`.

## Next steps / чеклист

1. **AppImage:** в `desktop/src-tauri/tauri.conf.json` в `bundle.targets` уже есть `"appimage"`. Сборка в toolbox: (1) установить linuxdeploy: `./scripts/install_linuxdeploy_toolbox.sh`, добавить `~/.local/bin` в PATH; (2) установить `librsvg2-devel`; (3) `export NO_STRIP=true APPIMAGE_EXTRACT_AND_RUN=1` и `cd desktop && npm run build && npm run tauri build` (подробно: [desktop-build-deps.md](desktop-build-deps.md) § AppImage). Артефакт: `desktop/src-tauri/target/release/bundle/appimage/VoiceForge_*_amd64.AppImage`. GA: скачать → `chmod +x` → запуск.
2. **Flatpak:** манифест `desktop/flatpak/com.voiceforge.app.yaml`, скрипт `scripts/build-flatpak.sh`; **сборка из корня репо:** `make flatpak-build`. Локальная установка после сборки: `flatpak-builder --user --install build desktop/flatpak/com.voiceforge.app.local.yaml && flatpak run com.voiceforge.app`. CI: при необходимости job в release.yml.
3. **Воспроизводимость и glibc:** для совместимости со старыми дистрибутивами собирать AppImage в Docker (образ на базе Ubuntu 20.04/22.04) или в GitHub Actions.

## Ссылки

- [Tauri 2 — AppImage](https://v2.tauri.app/distribute/appimage)
- [Tauri 2 — Flatpak / Flathub](https://v2.tauri.app/distribute/flatpak/)
- [Tauri 2 — Linux Code Signing](https://v2.tauri.app/distribute/sign/linux)
