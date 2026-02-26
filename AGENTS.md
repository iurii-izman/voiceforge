# AGENTS.md

## Cursor Cloud specific instructions

### Project overview

VoiceForge is a local-first AI assistant for Linux audio meetings. The Python backend (`src/voiceforge/`) is the core — managed by `pyproject.toml` + `uv`. An optional Tauri desktop app lives in `desktop/`.

### Running services

- **CLI**: `uv run voiceforge <command>` (status, history, cost, export, etc.)
- **Web UI**: `uv run voiceforge web --port 8765` — local HTTP server with REST API at `/api/*`
- **Daemon**: `uv run voiceforge daemon` — D-Bus daemon for desktop app integration
- Audio capture (`listen`) requires PipeWire, which is unavailable in cloud VMs

### Lint / Test / Build

Standard commands are in `README.md` and `Makefile`:

- **Lint**: `uv run ruff check src tests scripts`
- **Tests**: `uv run pytest tests -q --ignore=tests/eval --ignore=tests/test_stt_integration.py`
  - Eval tests (`tests/eval/`) and STT integration tests (`tests/test_stt_integration.py`) require models/APIs and should be excluded in CI-like environments
- **Build**: `uv build --wheel`
- **Full PR verification**: `./scripts/verify_pr.sh`

### Gotchas

- One pre-existing test failure in `test_cli_index_watch_smoke_with_mocks`: the test sets `VOICEFORGE_LANGUAGE=ru` but the i18n module returns English strings. This is a known issue — skip with `-k "not test_cli_index_watch_smoke_with_mocks"` if needed.
- `uv` must be on PATH. If freshly installed via `curl -LsSf https://astral.sh/uv/install.sh | sh`, add `$HOME/.local/bin` to PATH.
- SQLite databases are auto-created under `$XDG_DATA_HOME/voiceforge/` on first use — no external DB setup required.
- Keyring-dependent features (API key storage) may not work in headless/cloud VMs. Tests mock keyring interactions so this does not block testing.
