# Фокус следующей итерации

Файл обновляется **агентом после каждой большой итерации** (см. `agent-context.md`). Новый чат может подтянуть контекст через `@docs/runbooks/next-iteration-focus.md`.

**Обновлено:** 2026-02-24

**Последняя итерация:** Релиз Alpha2 закрыт — тег `v0.2.0-alpha.1` создан и запушен на origin. В `desktop-build-deps.md` добавлена секция «Полная последовательность в toolbox»: пакеты (или setup-desktop-toolbox.sh) → check-desktop-deps → `cd desktop && npm run build && cargo tauri build`. pyannote 4.0.4 оставлен; Flatpak и E2E — по желанию.

---

## Сверка плана развития (development-plan-post-audit-2026.md)

- **Часть I (все 10 пунктов)** и **блоки Alpha2 A–D** (Tauri, D-Bus, UI, streaming CLI) — реализованы. Детальная сверка: `docs/runbooks/claude-proposal-alignment.md`.
- **Часть II:** W1–W6, W7, W8, W9, W10 закрыты. W5 — retry в router; W6 — i18n для ошибок/шаблонов/action_items help; W10 — unit-тесты с моками в test_daemon_streaming_smart_trigger_model_manager.py.
- **Часть III** в development-plan: приоритеты на ближайшее время (релиз Alpha2, сборка десктопа в toolbox, pyannote, сигналы, Flatpak, E2E).

---

## Рекомендательные приоритетные задачи (что делать дальше)

1. **Релиз Alpha2 (Блок F):** выполнен — тег `v0.2.0-alpha.1` запушен на origin (release.md).
2. **Сборка десктопа в toolbox:** полная последовательность в `desktop-build-deps.md` (раздел «Полная последовательность в toolbox»): пакеты или `./scripts/setup-desktop-toolbox.sh` → `./scripts/check-desktop-deps.sh` → `cd desktop && npm run build && cargo tauri build`. В среде без webkit/gtk — только внутри toolbox.
3. **Согласовать версию pyannote:** в коде оставлена 4.0.4; при проблемах (OOM и т.д.) — зафиксировать в доке или откатить зависимость.
4. **Подписка на D-Bus-сигналы** в десктопе реализована; Flatpak и E2E — по желанию после стабильной сборки.
5. **Контракт D-Bus:** при изменении методов/сигналов обновлять desktop/DBUS.md и config-env-contract.md.

---

## Важные/критические проблемы на следующую итерацию

1. **Версия pyannote:** оставлена 4.0.4; при падениях/OOM — пересмотреть (доки или откат до 3.3.2).
2. **Сборка без cc/webkit:** десктоп собирается только в toolbox/окружении с зависимостями из desktop-build-deps.md.
3. **Экспорт из десктопа:** через CLI `voiceforge export`; для альфа2 достаточно; позже — ExportSession в D-Bus.
4. **ADR-0001:** новые команды CLI — только через ADR.

---

## Общий совет

Предложение Claude совпадает с нашей философией и ограничениями; план скорректирован без изменения архитектуры. Десктоп — основной UI через D-Bus; браузерное UI опционально. Для установки и запуска один вход: [installation-guide.md](installation-guide.md). Следующий шаг — закрыть релиз Alpha2; pyannote 4.0.4 оставлен, при проблемах — пересмотреть.
