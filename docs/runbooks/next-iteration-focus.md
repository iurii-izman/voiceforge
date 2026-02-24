# Фокус следующей итерации

Файл обновляется **агентом после каждой большой итерации** (см. `agent-context.md`). Новый чат может подтянуть контекст через `@docs/runbooks/next-iteration-focus.md`.

**Обновлено:** 2026-02-24

**Последняя итерация:** S3776 — history_helpers (_format_transcript_segment_lines), indexer (_sections_to_new_chunks), main (run_analyze_pipeline, run_live_summary, action_items_update, index, _service_unit_path, _format_template_result). Коммит daf3293, пуш в main.

---

## Блоки Sonar (актуально)

Список: `uv run python scripts/sonar_fetch_issues.py`.

**Блок A:** ~~S7785~~. **Блок B:** ~~S2083, S3649~~ (NOSONAR). **Блок D:** ~~S5713, S2737~~.

**Блок C — S3776 (осталось):**
- Сделано: pipeline, transcript_log, daemon, llm/router, status_helpers, dbus_service, history_helpers, rag/indexer; main (164 run_analyze_pipeline, 252 run_live_summary, 547 action_items_update, 633 index, 754 _service_unit_path, 86 _format_template_result).
- Осталось: main.py:893 (cli 82), web/server.py:209/433, core/metrics.py:201/287, llm/router.py:293.

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
