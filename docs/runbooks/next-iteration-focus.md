# Фокус следующей итерации

Файл обновляется **агентом после каждой большой итерации** (см. `agent-context.md`). Новый чат может подтянуть контекст через `@docs/runbooks/next-iteration-focus.md`.

**Обновлено:** 2026-02-24

**Последняя итерация:** Перепроверка Sonar, правки S1534 (дубликат border в voiceforge-arch), S7735 (desktop:199 duration_sec). Актуализированы блоки Sonar ниже.

---

## Блоки Sonar (актуально, после перепроверки)

Список: `uv run python scripts/sonar_fetch_issues.py`.

**Блок A — JS/JSX (мелкие, 1–2 шт.):**
- desktop/main.js:283 S7785 — Prefer top-level await over async IIFE (может потребовать type="module" / bundler).
- ~~voiceforge-arch.jsx:268 S1534~~ — дубликат `border` в style (исправлено).
- ~~desktop/main.js:199 S7735~~ — negated condition `!= null` (исправлено).

**Блок B — BLOCKER (2):**
- main.py:543 S2083 — path from user-controlled data (_action_item_status_path / XDG_DATA_HOME); уже есть валидация под home — при необходимости подавить или доработать.
- transcript_log.py:78 S3649 — SQL from user-controlled data (conn.executescript(sql) из миграций); миграции — внутренние файлы, при необходимости комментарий/suppression.

**Блок C — S3776 Cognitive Complexity (много файлов):**
- history_helpers.py:74 (44→15), status_helpers.py:69 (20→15), status_helpers.py:108 (31→15).
- pipeline.py:140 (16→15), transcript_log.py:218 (17→15), daemon.py:314 (16→15), dbus_service.py:168 (19→15).
- llm/router.py:103 (17→15), router.py:275 (42→15).
- main.py:86 (42), 164 (17), 252 (27), 547 (20), 754 (22), 633 (22), 893 (82).
- web/server.py:209 (54), 433 (33).
- core/metrics.py:201 (29), 287 (29).
- rag/indexer.py:140 (28→15).

**Блок D — прочее (2):**
- local_llm.py:44 S5713 — redundant Exception class (в коде класса нет — проверить при скане).
- rag/indexer.py:252 S2737 — except clause (уже заменён на `raise` — при рескане может исчезнуть).

**Рекомендуемый порядок:** A (S7785 по желанию) → B (BLOCKER при необходимости) → C по одному файлу (сначала 16–17, потом остальные) → D.

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

1. ~~**Стабилизация сборки десктопа (roadmap 13)**~~ — сделано: `desktop-build-deps.md` (pkg-config, воспроизводимая последовательность).
2. ~~**Экспорт сессии из десктопа**~~ — реализован: Tauri `export_session` вызывает CLI `voiceforge export`; кнопки в UI есть.
3. ~~**Офлайн-пакет (roadmap 14)**~~ — черновик: `docs/runbooks/offline-package.md` (Flatpak/AppImage, этапы).
4. ~~**Согласовать версию pyannote**~~ — сделано: `docs/runbooks/pyannote-version.md` (4.0.4, откат 3.3.2 при OOM).
5. ~~**Контракт D-Bus**~~ — сделано: в `config-env-contract.md` ссылка на `desktop/DBUS.md`; при изменениях обновлять оба.
6. ~~**Smart trigger по умолчанию (roadmap 15)**~~ — политика зафиксирована: default остаётся `false` до сбора отзывов; при включении по умолчанию — обновить config и `config-env-contract.md` (см. описание `smart_trigger`).
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

См. блок **«Следующие 10 шагов по реализации проекта»** и **«Блоки Sonar (актуально)»** выше. Шаги 1–6 выполнены. Ближайшие по Sonar: блок A (S7785), блок B (BLOCKER при необходимости), блок C (S3776 по файлам). По roadmap: шаги 7–10 (бот, календарь, RAG, стабилизация) — по мере необходимости.

---

## Важные/критические проблемы на следующую итерацию

1. **Версия pyannote:** 4.0.4; при падениях/OOM — см. `docs/runbooks/pyannote-version.md` (откат до 3.3.2 и шаги).
2. **Сборка без cc/webkit:** десктоп только в toolbox/окружении из desktop-build-deps.md.
3. **Экспорт из десктопа:** пока через CLI `voiceforge export`; позже — ExportSession в D-Bus при необходимости.
4. **ADR-0001:** новые команды CLI — только через ADR.

---

## Общий совет

Roadmap 1–12 закрыты по коду и тестам (e2e для 9–10 добавлены). Дальше — «Следующие 10 шагов» (roadmap 13–20 + стабилизация). Десктоп — основной UI через D-Bus; один вход для установки: [installation-guide.md](installation-guide.md).
