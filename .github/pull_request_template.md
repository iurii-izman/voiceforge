## Summary

<!-- What changed and why -->

## Change type (Conventional Commits)

- [ ] feat
- [ ] fix
- [ ] chore
- [ ] docs
- [ ] refactor
- [ ] test

Commit message: `type(scope): description` — see [git-github-practices](https://github.com/iurii-izman/voiceforge/blob/main/docs/runbooks/git-github-practices.md). Use `Closes #N` in body when fixing an issue.

## Definition Of Done (alpha0.1)

- [ ] I ran `./scripts/verify_pr.sh`
- [ ] I ran `./scripts/smoke_clean_env.sh`
- [ ] CLI contract is unchanged (see `tests/test_cli_surface.py`) or intentionally updated with explicit note
- [ ] DB migration behavior on clean and existing DB is covered by tests
- [ ] Config/env contract docs are up to date (`docs/runbooks/config-env-contract.md`)
- [ ] `CHANGELOG.md` updated for user-visible changes
- [ ] No secrets in changed files (gitleaks-safe)

## Risk & Rollback

<!-- Main risks and how to rollback if needed -->
