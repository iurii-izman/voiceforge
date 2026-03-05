## Summary

<!-- What changed and why -->

## Change Type

- [ ] feat
- [ ] fix
- [ ] chore
- [ ] docs
- [ ] refactor
- [ ] test

## Definition of Done

- [ ] `./scripts/verify_pr.sh` (or equivalent checks in CI)
- [ ] CLI contract unchanged or updated with note ([tests/test_cli_surface.py](../../tests/test_cli_surface.py))
- [ ] DB migration behavior covered ([tests/test_db_migrations.py](../../tests/test_db_migrations.py))
- [ ] Config/env docs updated if needed ([docs/runbooks/config-env-contract.md](../../docs/runbooks/config-env-contract.md))
- [ ] CHANGELOG updated for user-visible changes
- [ ] No secrets in changed files (gitleaks-safe)

## Risk & Rollback

<!-- Main risks and how to rollback if needed -->
