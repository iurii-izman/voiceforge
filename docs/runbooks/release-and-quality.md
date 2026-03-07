# Релизы и качество (объединённый runbook)

Единый документ: процесс релиза, откат, чеклисты альфа, Definition of Done. Объединяет бывшие release.md, rollback-alpha-release.md, alpha2-checklist.md, alpha0.1-dod.md.

---

## 1. Release runbook

**Версии:** Python package `0.1.0a1`; тег `v0.1.0-alpha.1`. Для альфа2: `0.2.0a1` / `v0.2.0-alpha.1`.

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

**Coverage #56:** текущий fail_under=72 (pyproject.toml). Цель 75→80%. Запуск полного отчёта: `make coverage` (рекомендуется в toolbox — в Cursor полный pytest может OOM). При достижении ≥75% выставить в pyproject.toml `fail_under = 75`.

**Для альфа2 (с десктопом):** версия 0.2.0a1; сборка десктопа: `cd desktop && npm run build && cargo tauri build`; артефакты в `desktop/src-tauri/target/release/bundle/`. Чеклист: сценарий «демон → Tauri → анализ → сессия»; CHANGELOG обновлён.

**Команды:**
```bash
./scripts/verify_pr.sh && ./scripts/smoke_clean_env.sh && ./scripts/check_cli_contract.sh
uv run pytest tests/test_db_migrations.py -q && uv build --wheel
./scripts/check_repo_governance.sh && ./scripts/check_new_code_coverage.sh
git tag -a v0.2.0-alpha.1 -m "VoiceForge alpha2: ..."
git push origin v0.2.0-alpha.1
```

**Ожидаемые артефакты:** `dist/*.whl`, Release workflow загружает SBOM (`dist/sbom.cdx.json`).

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

Версия **0.2.0a1** / тег **v0.2.0-alpha.1**.

**Перед тегом:** тесты CLI/демона; десктоп собирается (`./scripts/check-desktop-deps.sh`, `cd desktop && npm install && npm run build && cargo tauri build`); сценарий «демон → Tauri → анализ → сессия» вручную; CHANGELOG обновлён; версии в pyproject.toml, desktop/package.json, tauri.conf.json согласованы.

**Релиз:** по разделу 1 этого runbook.

---

## 4. Alpha0.1 Definition of Done

Сборка готова к alpha0.1, когда выполнено:

**Baseline:** git baseline + тег; дерево src/, tests/, docs/, scripts/; файлы .gitignore, .bandit.yaml, .gitleaks.toml, .pre-commit-config.yaml, .semgrepignore; workflows test, semgrep, gitleaks, codeql, release.

**CLI/API:** `voiceforge --help` — 9 команд (listen, analyze, status, history, index, watch, daemon, install-service, uninstall-service); удалённые команды — "No such command"; JSON status: schema_version, ok, data (ram, cost_today_usd, ollama_available).

**Качество и безопасность:** verify_pr.sh, smoke_clean_env.sh, check_cli_contract.sh — OK; тесты db_migrations — OK; check_new_code_coverage.sh; CVE-2025-69872 временно в ignore до фикса upstream.

**Release readiness:** версия 0.1.0a1 / тег v0.1.0-alpha.1; шаги release runbook выполнены; CHANGELOG актуален.

**Перед бета-релизом:** привести в порядок Sonar и GitHub по чеклисту [pre-beta-sonar-github.md](pre-beta-sonar-github.md).
