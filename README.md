# VoiceForge

VoiceForge is a local-first assistant for audio meetings on Linux.

Current alpha line: `0.2.0-alpha.2` (`0.2.0a2` Python package version).

## Alpha0.1 Core

Core CLI commands:
- `listen` (optional `--stream`, `--live-summary`)
- `analyze` (optional `--template`: standup, sprint_review, one_on_one, brainstorm, interview)
- `status`
- `history` (list or `--id N` for detail)
- `cost` (cost report by days or `--from`/`--to`)
- `export` (session to md/pdf, optional `--clipboard`)
- `daily-report` (daily digest: sessions, action items, cost; optional `--llm`)
- `action-items update` (from-session / next-session)
- `index`, `watch`
- `daemon`
- `install-service`, `uninstall-service`
- `web` (local Web UI)

**Shell completion:** `voiceforge --install-completion bash` (or `zsh`). Add the emitted line to your shell rc.

## Requirements

- Linux with PipeWire
- Python 3.12+
- `uv`
- API keys in keyring (`anthropic`, `openai`, `huggingface`)

## Quick Start

```bash
./scripts/bootstrap.sh
uv sync --extra all
uv run voiceforge status
```

`uv sync --extra all` is the full-stack install profile: RAG, LLM, PII, calendar, OTel, and async web (`web-async`).

Core flow:

```bash
# Terminal 1
uv run voiceforge listen

# Terminal 2
uv run voiceforge analyze --seconds 30
uv run voiceforge history
```

Daemon mode:

```bash
uv run voiceforge daemon
```

## Development

```bash
uv run ruff check src tests scripts
uv run pytest tests -q
./scripts/verify_pr.sh
./scripts/smoke_clean_env.sh
./scripts/doctor.sh
# or:
make verify
make smoke
make release-check
```

Contribution/process:
- `CONTRIBUTING.md`
- `.github/pull_request_template.md`
- `CHANGELOG.md`

## Documentation

- `docs/README.md`
- `docs/first-meeting-5min.md` — quick start (5 min)
- `docs/plans.md` — планы, приоритет фич (roadmap 1–19), текущие задачи
- `docs/runbooks/agent-context.md` — agent context
- `docs/runbooks/web-api.md` — Web UI API contract
- `docs/architecture/overview.md`
- `docs/architecture/runtime-flow.md`
- `docs/runbooks/bootstrap.md`
- `docs/runbooks/security.md`
- `docs/runbooks/release.md`
- `docs/runbooks/config-env-contract.md`
- `docs/runbooks/repo-governance.md`
- `docs/runbooks/rollback-alpha-release.md`
- `docs/runbooks/test-operations.md`
- `docs/adr/`
