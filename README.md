# VoiceForge

**Local-first AI assistant for audio meetings on Linux.** PipeWire → STT → diarization → RAG → LLM. CLI + Tauri desktop with push-to-capture Knowledge Copilot: your documents, your answers, in real time.

**Current release:** `1.0.0-beta.1` ([Changelog](CHANGELOG.md))

---

## What it does

- **CLI:** Record, transcribe, analyze meetings; RAG index; cost reports; export; daemon; local Web UI.
- **Desktop (Tauri):** Tray app, push-to-capture hotkey, overlay with RAG-first cards (Evidence, Answer, Do/Don't, Clarify). No always-on recording; audio stays on your machine.
- **Knowledge Copilot:** Hold hotkey → capture a question → release → get instant cards from your documents (RAG) + optional LLM. Hybrid (local STT/RAG + cloud LLM) or offline.

---

## Requirements

- **Linux** with PipeWire
- **Python 3.12+**
- **[uv](https://docs.astral.sh/uv/)** for install
- **API keys** in system keyring (optional for cloud LLM): `anthropic`, `openai`, `huggingface` — see [keyring reference](docs/runbooks/keyring-keys-reference.md)

---

## Quick start

```bash
git clone https://github.com/iurii-izman/voiceforge.git && cd voiceforge
./scripts/bootstrap.sh
uv sync --extra all
uv run voiceforge status
```

**Daemon + desktop (e.g. in [toolbox](docs/runbooks/installation-guide.md) on Fedora Atomic):**

```bash
# Terminal 1
uv run voiceforge daemon

# Terminal 2
cd desktop && npm install && npm run tauri dev
```

**CLI-only flow:**

```bash
uv run voiceforge listen
# In another terminal:
uv run voiceforge analyze --seconds 30
uv run voiceforge history
```

Full install and rebuild guide: [docs/runbooks/rebuild-run-test-guide.md](docs/runbooks/rebuild-run-test-guide.md) (toolbox paths), [docs/runbooks/installation-guide.md](docs/runbooks/installation-guide.md).

---

## Documentation

- **Index (what to read):** [docs/DOCS-INDEX.md](docs/DOCS-INDEX.md)
- **First run (5 min):** [docs/first-meeting-5min.md](docs/first-meeting-5min.md)
- **Quickstart:** [docs/runbooks/quickstart.md](docs/runbooks/quickstart.md)
- **Config & keyring:** [docs/runbooks/config-env-contract.md](docs/runbooks/config-env-contract.md), [docs/runbooks/keyring-keys-reference.md](docs/runbooks/keyring-keys-reference.md)
- **Desktop build (toolbox):** [docs/runbooks/desktop-build-deps.md](docs/runbooks/desktop-build-deps.md)
- **Releases & quality:** [docs/runbooks/release-and-quality.md](docs/runbooks/release-and-quality.md)

---

## Development

```bash
uv run ruff check src tests scripts
uv run pytest tests/ -q --tb=line
./scripts/verify_pr.sh
./scripts/doctor.sh
```

- **Contributing:** [CONTRIBUTING.md](CONTRIBUTING.md)
- **Security:** [SECURITY.md](SECURITY.md)
- **PR template:** [.github/pull_request_template.md](.github/pull_request_template.md)

---

## License

MIT. See [LICENSE](LICENSE).
