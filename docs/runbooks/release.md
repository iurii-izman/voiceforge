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
8. SonarCloud check-run is green for `origin/main` (`./scripts/check_sonar_status.sh --required`).
9. Governance baseline is green (`./scripts/check_repo_governance.sh`).
10. New-code coverage gate passes (`./scripts/check_new_code_coverage.sh`).

Release commands:

```bash
./scripts/verify_pr.sh
./scripts/smoke_clean_env.sh
./scripts/check_cli_contract.sh
uv run pytest tests/test_db_migrations.py -q
uv build --wheel
./scripts/check_sonar_status.sh --required
./scripts/check_repo_governance.sh
./scripts/check_new_code_coverage.sh
git tag -a v0.1.0-alpha.1 -m "voiceforge alpha0.1"
```

Expected outputs:

1. `verify_pr.sh: ALL CHECKS PASSED`
2. `smoke_clean_env.sh: OK`
3. `uv build --wheel` produces `dist/*.whl`
4. Release workflow uploads `dist/sbom.cdx.json` (CycloneDX SBOM)

Rollback:
- `docs/runbooks/rollback-alpha-release.md`
