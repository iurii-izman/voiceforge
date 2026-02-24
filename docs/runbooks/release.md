# Release Runbook

Version line:
- Python package: `0.1.0a1`
- Git tag format: `v0.1.0-alpha.1`

Pre-release checklist:
1. `./scripts/verify_pr.sh` passes.
2. `./scripts/smoke_clean_env.sh` passes.
3. `./scripts/check_cli_contract.sh` passes.
4. DB migration tests pass (`uv run pytest tests/test_db_migrations.py -q`).
5. Draft release exists and notes are up to date (workflow `Release Draft`).
6. `uv build --wheel` succeeds.
7. Version and tag line are aligned (`0.1.0a1` / `v0.1.0-alpha.1`).
8. (Опционально) SonarCloud — только справочно; чек не блокирует (см. repo-governance.md).
9. Governance baseline is green (`./scripts/check_repo_governance.sh`).
10. New-code coverage gate passes (`./scripts/check_new_code_coverage.sh`, порог по умолчанию 20%; на поздних этапах поднимать).

**Для альфа2 (с десктопом):**
- Версия: 0.2.0a1 (pyproject.toml и desktop/ в согласовании с тегом `v0.2.0-alpha.1`).
- Сборка десктопа: `cd desktop && npm run build && cargo tauri build`; артефакты в `desktop/src-tauri/target/release/bundle/`. При наличии Flatpak — шаг сборки Flatpak по инструкции в `desktop/` или `docs/runbooks/desktop-build-deps.md`.
- Чеклист: сценарий «запуск демона → запуск Tauri → анализ → просмотр сессии» выполняется; CHANGELOG обновлён.

Release commands:

```bash
./scripts/verify_pr.sh
./scripts/smoke_clean_env.sh
./scripts/check_cli_contract.sh
uv run pytest tests/test_db_migrations.py -q
uv build --wheel
./scripts/check_repo_governance.sh
./scripts/check_new_code_coverage.sh
git tag -a v0.1.0-alpha.1 -m "voiceforge alpha0.1"
```

Для альфа2 (тег после коммита с версией 0.2.0a1 и обновлённым CHANGELOG):

```bash
git tag -a v0.2.0-alpha.1 -m "VoiceForge alpha2: desktop Tauri, D-Bus, streaming CLI"
git push origin v0.2.0-alpha.1
```

Expected outputs:

1. `verify_pr.sh: ALL CHECKS PASSED`
2. `smoke_clean_env.sh: OK`
3. `uv build --wheel` produces `dist/*.whl`
4. Release workflow uploads `dist/sbom.cdx.json` (CycloneDX SBOM)

Rollback:
- `docs/runbooks/rollback-alpha-release.md`
