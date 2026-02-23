# Alpha0.1 Definition of Done

A build is considered ready for alpha0.1 only when all checks below are true.

## Baseline integrity

1. Git baseline exists with at least one commit and a baseline tag.
2. Core project tree exists: `src/`, `tests/`, `docs/`, `scripts/`.
3. Security/tooling files exist:
   - `.gitignore`
   - `.bandit.yaml`
   - `.gitleaks.toml`
   - `.pre-commit-config.yaml`
   - `.semgrepignore`
4. CI workflow set exists:
   - `.github/workflows/test.yml`
   - `.github/workflows/semgrep.yml`
   - `.github/workflows/gitleaks.yml`
   - `.github/workflows/codeql.yml`
   - `.github/workflows/release.yml`

## CLI/API contract

1. `uv run voiceforge --help` shows exactly 9 core commands:
   - `listen`
   - `analyze`
   - `status`
   - `history`
   - `index`
   - `watch`
   - `daemon`
   - `install-service`
   - `uninstall-service`
2. Removed commands fail with "No such command" (for example `tasks`).
3. JSON status contract remains stable:
   - top-level fields: `schema_version`, `ok`, `data`.
   - `data` contains `ram`, `cost_today_usd`, `ollama_available`.

## Quality and security gates

1. `./scripts/verify_pr.sh` passes.
2. `./scripts/smoke_clean_env.sh` passes.
3. `./scripts/check_cli_contract.sh` passes.
4. DB migrations tests pass (`uv run pytest tests/test_db_migrations.py -q`).
5. New-code coverage gate passes (`./scripts/check_new_code_coverage.sh`, default 20%; поднимать на поздних этапах).
6. Security scans pass with current temporary exception:
   - `CVE-2025-69872` is ignored until upstream fix is released.

## Release readiness

1. Version values are aligned:
   - package version `0.1.0a1`
   - release tag `v0.1.0-alpha.1`
2. Release runbook steps in `docs/runbooks/release.md` are complete.
3. `CHANGELOG.md` includes current release notes.
