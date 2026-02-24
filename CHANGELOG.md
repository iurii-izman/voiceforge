# Changelog

All notable changes to this project are documented in this file.

The format is based on Keep a Changelog and this project follows SemVer pre-release tags.

## [Unreleased]

_No changes yet._

## [0.2.0-alpha.1] - 2026-02-24

### Added

- **Десктопный UI (Tauri, Roadmap #13):** приложение в `desktop/` — Tauri 2 + D-Bus-клиент к демону `com.voiceforge.App`. Экраны: Главная (статус демона, старт/стоп записи, анализ с секундами и шаблоном, стриминг), Сессии (список, детали, экспорт Markdown/PDF через CLI), Затраты (GetAnalytics 7d/30d), Настройки (только чтение). Архитектура: ADR-0004; зависимости и проверка окружения: `docs/runbooks/desktop-build-deps.md`, `scripts/check-desktop-deps.sh`. Контракт D-Bus: `desktop/DBUS.md`.
- **PII UX (Roadmap #11):** в вывод `status` (текст и `--output json`) добавлен текущий режим PII (`pii_mode`: OFF/ON/EMAIL_ONLY). Ключ i18n `status.pii_mode`. Контракт: config-env-contract.md (CLI status включает pii_mode).
- **Расширенные e2e (#8):** тесты `test_cli_cost_from_to_smoke` (cost --from/--to --output json), `test_cli_status_detailed_json_smoke` (status --detailed --output json), `test_cli_doctor_json_smoke` (status --doctor --output json); в `test_cli_cost_status_smoke` — проверка `pii_mode` в status.
- **Локализация e2e:** в тестах, проверяющих русский вывод (index/watch, export md, history --output md), задаётся `VOICEFORGE_LANGUAGE=ru` для стабильных проверок независимо от LANG.
- **Live summary (Roadmap #10):** интервал и окно настраиваются через `live_summary_interval_sec` (env `VOICEFORGE_LIVE_SUMMARY_INTERVAL_SEC`, default 90). Используется в `listen --live-summary` (каждые N с по последним N с).
- **Явный язык для STT (Roadmap #7):** `VOICEFORGE_LANGUAGE` (ru/en) передаётся в Whisper как hint в CLI `listen` (стриминг) и в демоне; при `auto` hint не передаётся.
- **Smart trigger template (Roadmap #15):** опциональная настройка `smart_trigger_template` (env `VOICEFORGE_SMART_TRIGGER_TEMPLATE`): при срабатывании авто-анализа демон передаёт шаблон в pipeline и сохраняет в лог сессии.
- **E2E:** тест `test_cli_history_output_md_smoke` — проверка вывода `history --id N --output md` (секции Сессия, Транскрипт, Анализ).
- **Cost report (Roadmap #6):** в текстовом выводе `cost` добавлена разбивка по моделям (как в `status --detailed`).

### Changed

- **listen --live-summary (Roadmap #10):** сообщение при включении показывает настроенный интервал (`live_summary_interval_sec`) в ru/en (i18n с плейсхолдером `{interval}`).
- **W4 GetSettings D-Bus:** в config-env-contract.md задокументировано: `privacy_mode` — алиас `pii_mode` (для совместимости UI).
- **W6 i18n:** оставшиеся пользовательские строки в `main.py` переведены на `t(key)`: ошибки, listen/analyze/action-items/index/watch/install-service/cost/export (ru/en).
- **Экспорт PDF:** в quickstart и first-meeting-5min явно указано, что PDF опционален и требует pandoc/pdflatex.

### Documentation

- **config-env-contract.md:** CLI status (и status --output json) включает `pii_mode` для PII UX; поле `live_summary_interval_sec`; раздел D-Bus GetSettings (privacy_mode = alias pii_mode); поле `smart_trigger_template`.
- **План развития (аудит фев 2026):** сверка с кодом выполнена — Часть I (1–10) и Часть II (W1–W3, W8) реализованы; добавлены валидаторы Settings: `ollama_model` (non-empty), `ring_seconds` (positive), `pyannote_restart_hours` (≥ 1). Тесты `tests/test_config_settings.py` для W8.
- **history --output md:** вывод детали сессии в Markdown при `history --id N --output md`; в Markdown (в т.ч. `export`) добавлена дата сессии (started_at). Сообщение об ошибке при `--output md` без `--id` выведено через i18n.
- **Action items (ADR-0002):** Отдельная таблица `action_items` (миграция 005), cross-session трекинг. Флаг `history --action-items` — список задач по сессиям; `action-items update` сохраняет статусы и в БД.
- **Unit-тесты (W10):** daemon (get_settings, get_analytics), smart_trigger, model_manager, streaming (см. `tests/test_daemon_streaming_smart_trigger_model_manager.py`).
- **config-env-contract.md:** источник правды для cost_usd (W9): metrics.db — тоталы и отчёты; transcripts.db — снимок стоимости по сессии. Обновлён дефолт `VOICEFORGE_IPC_ENVELOPE`.

- Sprint hardening: contributing/process docs, CI hardening, release draft and SBOM automation, DB migration tests, doctor script.
- **10 improvements (priorities 1–12):** Web UI: template & seconds in analyze, export (md/pdf), cost report, action-items update. Daemon/D-Bus: optional template in Analyze. Session log: template in analyses (migration 004), shown in export/history. E2E tests: export, analyze --template, action-items update. Docs: first-meeting-5min (cost, action-items, settings), web-api contract. Local Web UI (`voiceforge web`).
- **Development plan (post-audit Feb 2026):** `status --detailed` (cost by model/day, budget %), `status --doctor` (environment diagnostics), `history --search TEXT` (FTS5), `history --date YYYY-MM-DD` and `--from`/`--to`, GetAnalytics D-Bus returns real metrics (e.g. last=7d/30d), RAG query context 200→1000 chars, Settings field validators (model_size, sample_rate, budget_limit_usd, timeout, default_llm), resampling to 16 kHz when `sample_rate` ≠ 16000 (pipeline), budget limit from Settings (removed hardcoded constant), runbook `docs/runbooks/quickstart.md`.

## [0.1.0-alpha.1] - 2026-02-21

### Added

- Baseline alpha0.1 core CLI (9 commands), quality gates, and release/tag baseline.

[Unreleased]: https://github.com/iurii-izman/voiceforge/compare/v0.2.0-alpha.1...HEAD
[0.2.0-alpha.1]: https://github.com/iurii-izman/voiceforge/compare/v0.1.0-alpha.1...v0.2.0-alpha.1
[0.1.0-alpha.1]: https://github.com/iurii-izman/voiceforge/releases/tag/v0.1.0-alpha.1
