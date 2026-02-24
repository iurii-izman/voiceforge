# Офлайн-пакет (Flatpak / AppImage) — roadmap 14

Черновик для упаковки десктопного приложения VoiceForge (Tauri 2) в форматы, не требующие установки системных пакетов на целевой машине.

## Зависимости и предпосылки

- **Сборка десктопа** уже воспроизводима в toolbox (см. `desktop-build-deps.md`): `./scripts/setup-desktop-toolbox.sh` → `cd desktop && npm run build && cargo tauri build`.
- Текущий `bundle.targets` в `desktop/src-tauri/tauri.conf.json`: `["deb", "rpm"]`. Для Flatpak/AppImage потребуется добавить цели или отдельные шаги сборки.
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
- **Этапы (черновик):**
  1. Установить flatpak и flatpak-builder; установить runtime (например `org.gnome.Platform//46`).
  2. Создать манифест в `desktop/flatpak/` (если директории нет — создать): описание приложения, SDK, зависимостей (webkit2gtk, gtk3 и т.д.).
  3. Сборка: `flatpak-builder build manifest.yml` (или аналог для Tauri 2).
  4. Локальный запуск: `flatpak-builder --run build manifest.yml com.voiceforge.app`.
  5. Публикация на Flathub — по правилам Flathub (ревизия манифеста, проверки).

## Рекомендация для альфа2

- Для альфа2 достаточно **бинарника из `cargo tauri build`** (deb/rpm или артефакты в `target/release/bundle/`); установка по `desktop-build-deps.md` и `installation-guide.md`.
- **Flatpak/AppImage** — после стабилизации ядра и десктопа: сначала выбрать один формат (например AppImage для простого раздачи одного файла или Flatpak для Flathub), затем описать полную последовательность в этом runbook и при необходимости скрипты в `scripts/`.

## Ссылки

- [Tauri 2 — AppImage](https://v2.tauri.app/distribute/appimage)
- [Tauri 2 — Flatpak / Flathub](https://v2.tauri.app/distribute/flatpak/)
- [Tauri 2 — Linux Code Signing](https://v2.tauri.app/distribute/sign/linux)
