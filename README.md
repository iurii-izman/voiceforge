# VoiceForge

VoiceForge is a local-first assistant for audio meetings on Linux.

Baseline: `0.1.0-alpha.1` (`0.1.0a1` Python package version).

## Alpha0.1 Core

Core CLI commands:
- `listen`
- `analyze`
- `status`
- `history`
- `index`
- `watch`
- `daemon`
- `install-service`
- `uninstall-service`

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
```

## Documentation

- `docs/README.md`
- `docs/architecture/overview.md`
- `docs/architecture/runtime-flow.md`
- `docs/runbooks/bootstrap.md`
- `docs/runbooks/security.md`
- `docs/runbooks/release.md`
- `docs/adr/`
