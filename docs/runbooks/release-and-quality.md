# Релизы и качество (объединённый runbook)

Единый документ: процесс релиза, откат, чеклисты альфа, Definition of Done. Объединяет бывшие release.md, rollback-alpha-release.md, alpha2-checklist.md, alpha0.1-dod.md.

---

## 1. Release runbook

**Версии:** текущая alpha2-линия — Python package `0.2.0a2`; тег `v0.2.0-alpha.2`.

**Чеклист перед релизом:**
1. `./scripts/verify_pr.sh` — OK
2. `./scripts/smoke_clean_env.sh` — OK
3. `./scripts/check_cli_contract.sh` — OK
4. DB migration tests: `uv run pytest tests/test_db_migrations.py -q`
5. Draft release и заметки актуальны (workflow Release Draft)
6. `uv build --wheel` — OK
7. Версия и тег согласованы
8. (Опционально) SonarCloud — справочно; не блокирует (см. repo-and-git-governance.md)
9. `./scripts/check_repo_governance.sh` — OK
10. New-code coverage: `./scripts/check_new_code_coverage.sh` (порог 20%; на поздних этапах поднимать)

**Coverage #56/#99:** fail_under=60 (pyproject.toml); `server.py` и `rag/watcher.py` уже выведены из omit (#99). Цель дальше — поднимать к 75→80%. Запуск: `make coverage` или `uv run pytest tests/ -q -m "not integration" --cov=src/voiceforge --cov-report=term` (рекомендуется в toolbox — в Cursor полный pytest может OOM).

**Coverage #99 incremental path:** для hotspot-модулей `server_async.py`, `daemon.py`, `router.py`, `main.py` добавлять дешёвые helper/smoke/regression tests без OOM-risk; выводить из omit по одному при стабильном targeted subset. `server.py` уже в отчёте (suite: `test_web_smoke.py`, `test_web_action_items_update.py`, `test_web_status_export_action_items.py`, `test_coverage_hotspots_batch99.py`). `rag/watcher.py` теперь тоже в отчёте: `tests/test_rag_watcher.py` + существующий `watch` smoke в `tests/test_cli_e2e_smoke.py` + CLI helper contract в `tests/test_cli_helpers_contracts.py`; локальная policy-проверка с временно снятым omit дала `91%` для `src/voiceforge/rag/watcher.py`, поэтому omit обновлён честно. Для `main.py` safe subset (`test_main_status_export_action_items.py`, `test_cli_e2e_smoke.py`, `test_cli_helpers_contracts.py`, `test_core_commands.py`, `test_coverage_hotspots_batch99.py`) пока даёт только `55%`, поэтому policy там без изменений. Для `core/daemon.py` добавлен suite `tests/test_daemon_helpers.py` (#109): хелперы `_streaming_language_hint`, `_pid_path`, `_event_start_in_window`, методы daemon get_settings/get_streaming_transcript/get_sessions/get_session_detail/get_indexed_paths/search_rag/get_analytics/status с моками, `_retention_purge_at_startup`, `_wire_daemon_iface`; локальная проверка покрытия дала ~29% — hotspot остаётся для следующих batch. Следующий ROI-candidate — `llm/router.py` или продолжение daemon (listen/analyze paths).

**Для alpha2 (с десктопом):** версия `0.2.0a2`; сборка десктопа: `cd desktop && npm run build && cargo tauri build`; артефакты в `desktop/src-tauri/target/release/bundle/`. Чеклист: сценарий «демон → Tauri → анализ → сессия»; CHANGELOG обновлён.

**Команды:**
```bash
./scripts/verify_pr.sh && ./scripts/smoke_clean_env.sh && ./scripts/check_cli_contract.sh
uv run pytest tests/test_db_migrations.py -q && uv build --wheel
./scripts/check_repo_governance.sh && ./scripts/check_new_code_coverage.sh
python scripts/check_release_metadata.py
git tag -a v0.2.0-alpha.2 -m "VoiceForge alpha2: ..."
git push origin v0.2.0-alpha.2
```

**Ожидаемые артефакты:** `dist/*.whl`, Release workflow загружает SBOM (`dist/sbom.cdx.json`).

---

### 1.1 Release validation (packaging/updater)

Перед тегом обязательны (blocking):

- **Версии и контракт упаковки:** `python scripts/check_release_metadata.py` — проверяет синхронизацию версий (pyproject.toml → package.json, tauri.conf.json, Cargo.toml, Flatpak manifest) и **контракт updater**: допустимо только состояние «updater отключён» (`pubkey` и `endpoints` пустые) или «updater готов» (оба заданы). См. [desktop-updater.md](desktop-updater.md) § 0.

Рекомендуется для альфа2 с десктопом:

- Сборка десктопа: `cd desktop && npm run build && cargo tauri build` или `make flatpak-build` (см. [offline-package.md](offline-package.md)).
- Честный статус: до появления ключей подписи и сервера обновлений updater остаётся явно отключённым в репо.

---

### 1.2 Desktop CI: blocking vs advisory

- **Blocking для релиза:** только `check_release_metadata.py` (включая packaging/updater contract). Он вызывается в CI job `quality` и должен проходить перед тегом.
- **Advisory в CI:** jobs `desktop-audit` (npm audit, cargo audit) и `desktop-a11y` (pa11y) выполняются с `continue-on-error: true` из-за принятых рисков (известные CVE без фикса) и нестабильности окружения a11y. Они не блокируют merge и релиз. Политика: при появлении критичных уязвимостей — исправить или задокументировать allowlist в [security-and-dependencies.md](security-and-dependencies.md).
- **Local release gate для desktop shell:** `cd desktop && npm run e2e:native` считается обязательным локальным Linux smoke перед desktop релизом, но пока не вынесен в CI из-за зависимости от `tauri-driver`, `WebKitWebDriver` и GUI-capable runner. Полная матрица automated/native/manual checks: [desktop-release-gate-matrix.md](desktop-release-gate-matrix.md).

---

## 2. Rollback (откат альфа-релиза)

**Когда:** сломанный wheel/runtime после тега; неверные release notes; security-проблема в артефакте.

**Шаги:**
1. Остановить распространение, пометить релиз недействительным.
2. Если релиз ещё draft — удалить draft и пересоздать с исправленного коммита.
3. Если релиз опубликован: патч-коммит на main → новый тег (не перетегировать) → опубликовать исправляющий альфа-тег.
4. Обновить CHANGELOG (заметка об откате и исправлении).
5. Зафиксировать инцидент в PR/issue (причина, превенция).

**Проверка после отката:** verify_pr.sh, smoke_clean_env.sh, wheel и SBOM, release notes помечают superseded/broken tag.

---

## 3. Чеклист альфа2

Версия **0.2.0a2** / тег **v0.2.0-alpha.2**.

**Перед тегом:** тесты CLI/демона; десктоп собирается (`./scripts/check-desktop-deps.sh`, `cd desktop && npm install && npm run build && cargo tauri build`); сценарий «демон → Tauri → анализ → сессия» вручную; CHANGELOG обновлён; версии в `pyproject.toml`, `desktop/package.json`, `desktop/src-tauri/tauri.conf.json`, `desktop/src-tauri/Cargo.toml`, Flatpak manifest согласованы; `python scripts/check_release_metadata.py` возвращает `release metadata OK`.

**Релиз:** по разделу 1 этого runbook.

---

## 4. Alpha0.1 Definition of Done

Сборка готова к alpha0.1, когда выполнено:

**Baseline:** git baseline + тег; дерево src/, tests/, docs/, scripts/; файлы .gitignore, .bandit.yaml, .gitleaks.toml, .pre-commit-config.yaml, .semgrepignore; workflows test, semgrep, gitleaks, codeql, release.

**CLI/API:** `voiceforge --help` — 9 команд (listen, analyze, status, history, index, watch, daemon, install-service, uninstall-service); удалённые команды — "No such command"; JSON status: schema_version, ok, data (ram, cost_today_usd, ollama_available).

**Качество и безопасность:** verify_pr.sh, smoke_clean_env.sh, check_cli_contract.sh — OK; тесты db_migrations — OK; check_new_code_coverage.sh; CVE-2025-69872 временно в ignore до фикса upstream.

**Release readiness:** версия 0.2.0a2 / тег v0.2.0-alpha.2; шаги release runbook выполнены; CHANGELOG актуален.

**Перед бета-релизом:** привести в порядок Sonar и GitHub по чеклисту [pre-beta-sonar-github.md](pre-beta-sonar-github.md).
