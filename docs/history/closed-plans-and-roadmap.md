# История: закрытые планы и roadmap (сверка с кодом)

Документ фиксирует **что уже сделано** по планам развития и roadmap. Последний аудит: 2026-02-26. Текущий фокус и открытые задачи — в [next-iteration-focus.md](../runbooks/next-iteration-focus.md). Маппинг новых задач: [audit-to-github-map.md](../audit/audit-to-github-map.md).

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

## Закрытые GitHub issues (старый план, #32–53)

Все issues по предыдущему плану развития (development-plan-post-audit-2026.md) закрыты, кроме #50 (macOS/WSL2). Сверка 2026-02-26 подтверждает: код реализован, тесты пройдены.

| Issue | Тема | Статус |
|---|---|---|
| #32 A1 | Eval harness (golden samples, ROUGE-L) | Закрыт |
| #33 A2 | Instructor retry (max_retries=3) | Закрыт |
| #34 A3 | Unit-тесты daemon/streaming/smart_trigger | Закрыт |
| #35 A4 | WAV integration тесты | Закрыт |
| #36 B1 | Observability (Prometheus, /metrics) | Закрыт |
| #37 B2 | pyannote memory guard (2GB) | Закрыт |
| #38 B3 | Budget enforcement (pre-call, daily limit) | Закрыт |
| #39 B4 | IPC envelope default | Закрыт |
| #40 B5 | CI cache (uv) | Закрыт |
| #41 C1 | Prompt management (файлы) | Закрыт |
| #42 C2 | RAG query keyword extraction | Закрыт |
| #43 C3 | Data retention policy | Закрыт |
| #44 C4 | Response caching (SQLite) | Закрыт |
| #45 C5 | Healthcheck /health | Закрыт |
| #46 D1 | Desktop D-Bus signals | Закрыт |
| #47 D2 | Telegram bot (webhook, push) | Закрыт |
| #48 D3 | Calendar CalDAV auto-context | Закрыт |
| #49 D4 | Flatpak packaging | Закрыт |
| #50 D5 | macOS / WSL2 | **Открыт** |
| #51 QW1 | scipy в base deps | Закрыт |
| #52 QW2 | i18n hardcoded strings | Закрыт |
| #53 QW3 | ThreadPoolExecutor single | Закрыт |

---

## Roadmap 13–20 (реализовано в коде)

| # | Направление | Где в коде / доказательство |
|---|-------------|-----------------------------|
| 13 | Десктоп (Tauri) | `desktop/`: Tauri 2, D-Bus client, UI screens |
| 14 | Офлайн-пакет | Flatpak manifest + build-flatpak.sh + AppImage скрипты |
| 15 | Smart trigger | `audio/smart_trigger.py`, default false в config |
| 16 | Telegram bot | ADR-0005, `web/server.py` webhook, runbook |
| 17 | Календарь (CalDAV) | `calendar/caldav_poll.py`, ADR-0006, auto-context |
| 18 | RAG ODT/RTF | `rag/parsers.py`, тесты в test_rag_parsers.py |
| 19 | Prompt caching | Не реализовано (research R6 в новом аудите) |
| 20 | macOS / WSL2 | Не реализовано (issue #50, Step 19 нового аудита) |

---

## Следующий слой: PROJECT_AUDIT_AND_ROADMAP (2026-02-26)

Новый аудит выявил 20 Weaknesses и 20 Steps (Phase A–D). Все 20 Steps — **не реализованы** на момент сверки 2026-02-26. Маппинг и issues: [docs/audit/audit-to-github-map.md](../audit/audit-to-github-map.md).
