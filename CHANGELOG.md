# Changelog

All notable changes to this project are documented in this file.

The format is based on Keep a Changelog and this project follows SemVer pre-release tags.

## [Unreleased]

### Added

- **План развития (аудит фев 2026):** сверка с кодом выполнена — Часть I (1–10) и Часть II (W1–W3, W8) реализованы; добавлены валидаторы Settings: `ollama_model` (non-empty), `ring_seconds` (positive), `pyannote_restart_hours` (≥ 1). Тесты `tests/test_config_settings.py` для W8.
- **history --output md:** вывод детали сессии в Markdown при `history --id N --output md`; в Markdown (в т.ч. `export`) добавлена дата сессии (started_at). Сообщение об ошибке при `--output md` без `--id` выведено через i18n.
- **Action items (ADR-0002):** Отдельная таблица `action_items` (миграция 005), cross-session трекинг. Флаг `history --action-items` — список задач по сессиям; `action-items update` сохраняет статусы и в БД.
- **Unit-тесты (W10):** daemon (get_settings, get_analytics), smart_trigger, model_manager, streaming (см. `tests/test_daemon_streaming_smart_trigger_model_manager.py`).

### Changed

- **Settings (W8):** валидация при загрузке: `ollama_model`, `ring_seconds`, `pyannote_restart_hours`; контракт в config-env-contract.md обновлён.
- **I.2 (plan):** при `listen` с `--stream` или `streaming_stt=true` partial/final транскрипт выводится в терминал в реальном времени (реализация проверена).
- **W2 (sample_rate):** в стриминге (CLI listen и daemon) при `sample_rate` ≠ 16 kHz аудио ресэмплируется в 16 kHz перед STT; при отсутствии scipy — предупреждение в лог.
- **W3 (RAG):** константа `RAG_QUERY_MAX_CHARS=1000` в pipeline; контекст запроса RAG — до 1000 символов транскрипта.
- **GetSettings D-Bus (W4):** в ответ добавлено поле `privacy_mode` (алиас `pii_mode`).
- **D-Bus (W7):** envelope по умолчанию включён (`VOICEFORGE_IPC_ENVELOPE=true`); для старых клиентов — `VOICEFORGE_IPC_ENVELOPE=false`.
- **LLM (W5):** при невалидном JSON от модели — один retry запрос перед падением.
- **i18n (W6):** в `main.py` ошибки и сообщения history используют `t(key)` (ru/en).

### Documentation

- **config-env-contract.md:** источник правды для cost_usd (W9): metrics.db — тоталы и отчёты; transcripts.db — снимок стоимости по сессии. Обновлён дефолт `VOICEFORGE_IPC_ENVELOPE`.

- Sprint hardening: contributing/process docs, CI hardening, release draft and SBOM automation, DB migration tests, doctor script.
- **10 improvements (priorities 1–12):** Web UI: template & seconds in analyze, export (md/pdf), cost report, action-items update. Daemon/D-Bus: optional template in Analyze. Session log: template in analyses (migration 004), shown in export/history. E2E tests: export, analyze --template, action-items update. Docs: first-meeting-5min (cost, action-items, settings), web-api contract. Local Web UI (`voiceforge web`).
- **Development plan (post-audit Feb 2026):** `status --detailed` (cost by model/day, budget %), `status --doctor` (environment diagnostics), `history --search TEXT` (FTS5), `history --date YYYY-MM-DD` and `--from`/`--to`, GetAnalytics D-Bus returns real metrics (e.g. last=7d/30d), RAG query context 200→1000 chars, Settings field validators (model_size, sample_rate, budget_limit_usd, timeout, default_llm), resampling to 16 kHz when `sample_rate` ≠ 16000 (pipeline), budget limit from Settings (removed hardcoded constant), runbook `docs/runbooks/quickstart.md`.

## [0.1.0-alpha.1] - 2026-02-21

### Added

- Baseline alpha0.1 core CLI (9 commands), quality gates, and release/tag baseline.

[Unreleased]: https://github.com/iurii-izman/voiceforge/compare/v0.1.0-alpha.1...HEAD
[0.1.0-alpha.1]: https://github.com/iurii-izman/voiceforge/releases/tag/v0.1.0-alpha.1
