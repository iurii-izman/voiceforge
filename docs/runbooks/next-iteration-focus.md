# Фокус следующей итерации

Файл обновляется **агентом после каждой большой итерации** (см. `agent-context.md`). Новый чат может подтянуть контекст через `@docs/runbooks/next-iteration-focus.md`.

**Обновлено:** 2026-02-24

**Последняя итерация:** Добавлены e2e smoke для roadmap 9–10 (listen --stream, listen --live-summary). Roadmap 1–12 закрыты по коду; выделены следующие 10 шагов по реализации (roadmap 13–20 + стабилизация).

---

## Roadmap 1–12: статус (сверка по коду)

| # | Направление | Статус |
|---|-------------|--------|
| 1 | Шаблоны встреч в `analyze` | ✓ `--template`, D-Bus, daemon, web |
| 2 | Обновление статусов action items по следующей встрече | ✓ `action-items update`, БД, Web API |
| 3 | Экспорт сессии (Markdown/PDF) | ✓ `export --format md/pdf`, e2e в test_cli_e2e_smoke |
| 4 | Выбор модели Ollama в конфиге | ✓ `ollama_model` в config, router, config-env-contract |
| 5 | Документация «Первая встреча за 5 минут» | ✓ `docs/first-meeting-5min.md` |
| 6 | Отчёты по затратам (cost report) | ✓ `cost --days/--from/--to`, GetAnalytics, API |
| 7 | Явный язык для STT | ✓ `language` в config, `language_hint` в Whisper |
| 8 | Расширенные e2e-тесты | ✓ export, analyze --template, action-items, history --output md |
| 9 | Стриминговый STT в CLI (listen) | ✓ `--stream`/`streaming_stt`, e2e test_cli_listen_stream_smoke |
| 10 | Live summary во время listen | ✓ `--live-summary`, e2e test_cli_listen_live_summary_smoke |
| 11 | Управление PII (вкл/выкл, только email) | ✓ `pii_mode` OFF/ON/EMAIL_ONLY в config и status |
| 12 | Простой локальный Web UI | ✓ web/server.py: статус, сессии, затраты, action-items, экспорт |

Дублировать реализацию не нужно.

---

## Следующие 10 шагов по реализации проекта

1. **Стабилизация сборки десктопа (roadmap 13)** — зафиксировать последовательность в toolbox в `desktop-build-deps.md`, при необходимости скрипт `setup-desktop-toolbox.sh` и `check-desktop-deps.sh`; убедиться, что сборка воспроизводима.
2. **Экспорт сессии из десктопа** — при необходимости добавить метод D-Bus ExportSession (или вызов CLI из Tauri) и кнопку экспорта в UI десктопа; пока достаточно CLI `voiceforge export`.
3. **Офлайн-пакет (roadmap 14)** — исследование и черновик: Flatpak или AppImage для Linux; описать в runbook зависимости и этапы сборки.
4. **Согласовать версию pyannote** — зафиксировать в `desktop-build-deps.md` или отдельном runbook: текущая 4.0.4; при OOM на 8 ГБ — откат на 3.3.2 и шаги отката.
5. **Контракт D-Bus** — при любом изменении методов/сигналов обновлять `desktop/DBUS.md` и `docs/runbooks/config-env-contract.md`; при необходимости — снапшот тестов контракта.
6. **Smart trigger по умолчанию (roadmap 15)** — опционально: рассмотреть включение `smart_trigger` по умолчанию в конфиге после сбора отзывов; при включении — обновить доки и default в config.
7. **Бот Telegram/Slack (roadmap 16)** — приоритет по желанию: ADR + черновик архитектуры (webhook, команды, интеграция с демоном/CLI).
8. **Интеграция с календарём (roadmap 17)** — исследование: CalDAV/Google Calendar, триггер «встреча началась» для listen/analyze; описать в runbook или ADR.
9. **RAG: новые форматы (roadmap 18)** — постепенно: поддержка ODT/RTF в индексаторе; при добавлении — тесты и обновление доков.
10. **Стабилизация и документация** — обновить `installation-guide.md` и `first-meeting-5min.md` при изменении CLI/конфига; рассмотреть перевод ключевых runbook на английский; при необходимости — prompt caching (roadmap 19), macOS/WSL2 (roadmap 20).

---

## Сверка плана развития (development-plan-post-audit-2026.md)

- **Часть I (все 10 пунктов)** и **блоки Alpha2 A–D** (Tauri, D-Bus, UI, streaming CLI) — реализованы. Детальная сверка: `docs/runbooks/claude-proposal-alignment.md`.
- **Часть II:** W1–W10 закрыты.
- **Часть III:** релиз Alpha2 выполнен; сборка в toolbox описана в desktop-build-deps.md.

---

## Рекомендательные приоритетные задачи (что делать дальше)

См. блок **«Следующие 10 шагов по реализации проекта»** выше. Ближайшие по приоритету: шаги 1–4 (сборка десктопа, экспорт из десктопа, офлайн-пакет, pyannote); затем 5–6 (контракт D-Bus, smart trigger); 7–10 — по мере необходимости.

---

## Важные/критические проблемы на следующую итерацию

1. **Версия pyannote:** 4.0.4; при падениях/OOM — пересмотреть (доки или откат до 3.3.2).
2. **Сборка без cc/webkit:** десктоп только в toolbox/окружении из desktop-build-deps.md.
3. **Экспорт из десктопа:** пока через CLI `voiceforge export`; позже — ExportSession в D-Bus при необходимости.
4. **ADR-0001:** новые команды CLI — только через ADR.

---

## Общий совет

Roadmap 1–12 закрыты по коду и тестам (e2e для 9–10 добавлены). Дальше — «Следующие 10 шагов» (roadmap 13–20 + стабилизация). Десктоп — основной UI через D-Bus; один вход для установки: [installation-guide.md](installation-guide.md).
