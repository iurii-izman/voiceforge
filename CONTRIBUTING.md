# Contributing to VoiceForge

VoiceForge is a local-first assistant for audio meetings (CLI + Tauri desktop). We keep changes minimal, testable, and reversible. Current line: **1.0.0-beta.1**.

## Branches

- Do not work directly on `main`.
- Use short-lived branches: `feat/...`, `fix/...`, `chore/...`, `docs/...`.
- Direct pushes to `main` are blocked by repo rules and pre-push hook.

## Commits

- Use [Conventional Commits](https://www.conventionalcommits.org/): `type(scope): summary`.
- Examples: `feat(desktop): overlay position`, `fix(cli): history json stability`, `docs(runbooks): update quickstart`.
- Include docs/tests in the same commit when behavior changes.
- Link issues: `Closes #123` or `Refs #124` in body when relevant.

## Pull requests

- Fill the [PR template](.github/pull_request_template.md).
- Before requesting review, run:
  - `./scripts/verify_pr.sh`
  - `./scripts/smoke_clean_env.sh`
- If you change CLI surface, DB schema, config/env, or release process, update the relevant docs and `CHANGELOG.md`.

## CLI and contracts

- Public CLI commands are part of the supported contract. See tests and [config-env-contract](docs/runbooks/config-env-contract.md) for the current set (e.g. `voiceforge --help`).
- Any new or removed CLI command needs explicit approval and doc update.

## Security

- Do not commit secrets. Use system keyring only; see [keyring-keys-reference](docs/runbooks/keyring-keys-reference.md).
- Run `./scripts/verify_pr.sh` (includes gitleaks, bandit, etc.).
- Security policy: [SECURITY.md](SECURITY.md). Dependencies and alerts: [security-and-dependencies](docs/runbooks/security-and-dependencies.md).

## Docs and runbooks

- Single source for “what doc to read”: [docs/DOCS-INDEX.md](docs/DOCS-INDEX.md).
- When adding or changing behavior, update the matching runbook and DOCS-INDEX if needed.
