# История: закрытые планы и roadmap (сверка с кодом)

Документ фиксирует **что уже сделано** по планам развития и roadmap. Аудит по коду выполнен 2026-02-24. Текущий фокус и открытые задачи — в [next-iteration-focus.md](../runbooks/next-iteration-focus.md).

---

## Roadmap 1–12 (реализовано в коде)

| # | Направление | Где в коде / доказательство |
|---|-------------|-----------------------------|
| 1 | Шаблоны встреч в `analyze` | `main.py`: `--template`, `_TEMPLATE_CHOICES`; `llm/router.py`: схемы + template; `web/server.py`: analyzeTemplate; `dbus_service.py` / `daemon.py`: template |
| 2 | Action items по следующей встрече | `action-items update`, миграция 005, `history_helpers`, `web/server.py` action-items/update |
| 3 | Экспорт сессии (Markdown/PDF) | `main.py`: `export_session()`, `--format md|pdf`; e2e в `test_cli_e2e_smoke.py` |
| 4 | Выбор модели Ollama в конфиге | `config.py`: `ollama_model`; router, config-env-contract |
| 5 | Документация «Первая встреча за 5 минут» | `docs/first-meeting-5min.md`, runbooks quickstart |
| 6 | Отчёты по затратам | `cost --days/--from/--to`, `get_stats`/`get_stats_range`, GetAnalytics D-Bus, Web API |
| 7 | Явный язык для STT | `config`: `language`, передача в Whisper `language_hint` |
| 8 | Расширенные e2e-тесты | export, analyze --template, action-items, history --output md в тестах |
| 9 | Стриминговый STT в CLI (listen) | `--stream`/`streaming_stt`, `_streaming_listen_worker` в main.py, e2e test_cli_listen_stream_smoke |
| 10 | Live summary во время listen | `--live-summary`, `run_live_summary_pipeline`, e2e test_cli_listen_live_summary_smoke |
| 11 | Управление PII | `pii_mode` OFF/ON/EMAIL_ONLY в config и status |
| 12 | Простой локальный Web UI | `web/server.py`: статус, сессии, затраты, action-items, экспорт |

---

## План развития (development-plan-post-audit-2026) — Часть I

Все 10 пунктов **реализованы** (сверка: claude-proposal-alignment.md и код):

- 1. `analyze --template` — см. roadmap #1.
- 2. Streaming в CLI listen — см. roadmap #9.
- 3. history --format md / export — см. roadmap #3.
- 4. `status --detailed` — get_status_detailed_* в status_helpers.
- 5. `history --search` — main.py `--search`, history_helpers search.
- 6. Action items DB + cross-session — миграция 005, action-items update, history --action-items.
- 7. `history --date`, `--from`/`--to` — main.py, history_helpers.
- 8. Quickstart / первая встреча за 5 мин — docs, runbooks.
- 9. GetAnalytics D-Bus — daemon.get_analytics, get_stats/get_stats_range, desktop GetAnalytics.
- 10. doctor как `status --doctor` — main.py `--doctor`, get_doctor_data/get_doctor_text.

---

## Блоки Alpha2 (A–D) и слабые места W1–W10

- **A–D:** Tauri каркас, D-Bus, UI (Главная/Сессии/Затраты/Настройки), streaming CLI — реализованы.
- **W1–W10:** по claude-proposal-alignment.md закрыты (budget из Settings, ресэмплинг, RAG 1000, privacy_mode/pii_mode, retry в router, i18n в main, envelope default, validators, source of truth в доке, тесты с моками).

---

## Sonar

Закрыто: S1192, S3626, S3358, S7785 (NOSONAR), все S3776 (рефакторинг server, main, history_helpers, metrics).

---

## Следующие 10 шагов — уже сделанное

1. Стабилизация сборки десктопа — desktop-build-deps.md, check-desktop-deps.sh.
2. Экспорт из десктопа — Tauri export_session → CLI voiceforge export.
3. Офлайн-пакет — черновик offline-package.md (Flatpak/AppImage в bundle.targets).
4. Согласовать версию pyannote — pyannote-version.md (4.0.4, откат при OOM).
5. Контракт D-Bus — config-env-contract.md ↔ desktop/DBUS.md.
6. Smart trigger по умолчанию — политика: default false, описание в config.

---

## Что здесь не перечислено

- **Roadmap 13:** десктоп (Tauri) — реализован.
- **Roadmap 14–20:** частично (Telegram бот — ADR-0005, webhook, runbook); календарь, RAG ODT/RTF, AppImage/Flatpak полный цикл, prompt caching, macOS/WSL2 — открытые или в плане.

Текущий список **не сделанного** и следующих шагов — в [next-iteration-focus.md](../runbooks/next-iteration-focus.md).
