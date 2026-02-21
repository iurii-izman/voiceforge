# Contributing (Lite)

VoiceForge keeps a small alpha0.1 scope. Changes must stay minimal, testable, and reversible.

## Branches

1. Never work directly on `main`.
2. Use short-lived branches: `feat/...`, `fix/...`, `chore/...`, `docs/...`.
3. Direct pushes to `main` are prohibited by policy (enforced via GitHub ruleset + local pre-push hook).

## Commits

1. Keep commits focused and small.
2. Preferred format: `type(scope): summary` (for example `fix(cli): keep history json stable`).
3. Include docs/tests in the same commit when behavior changes.

## Pull Requests

1. Fill PR template fully.
2. Required before review:
   - `./scripts/verify_pr.sh`
   - `./scripts/smoke_clean_env.sh`
3. If CLI contract, DB schema, config/env contract, or release process changed, update docs and `CHANGELOG.md`.

## CLI Contract Guardrails

For alpha0.1, keep exactly 9 public CLI commands:

- `listen`
- `analyze`
- `status`
- `history`
- `index`
- `watch`
- `daemon`
- `install-service`
- `uninstall-service`

Any CLI surface change requires explicit approval and a contract update.

## Security Basics

1. Do not commit secrets.
2. Keep credentials in keyring only.
3. Run security checks from `./scripts/verify_pr.sh`.
