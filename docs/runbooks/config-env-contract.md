# Config and Env Contract (alpha0.1)

Source of truth: `src/voiceforge/core/config.py`.

Priority order:
1. CLI/runtime explicit values (when applicable)
2. Environment variables (`VOICEFORGE_*`)
3. `voiceforge.yaml` (`$XDG_CONFIG_HOME/voiceforge/voiceforge.yaml` or `./voiceforge.yaml`)
4. Built-in defaults

## Settings Fields

| Field | Env var | Default | Description |
|---|---|---|---|
| `model_size` | `VOICEFORGE_MODEL_SIZE` | `small` | `faster-whisper` model size |
| `sample_rate` | `VOICEFORGE_SAMPLE_RATE` | `16000` | Audio sample rate (Hz) |
| `default_llm` | `VOICEFORGE_DEFAULT_LLM` | `anthropic/claude-haiku-4-5` | LLM id for `analyze` |
| `budget_limit_usd` | `VOICEFORGE_BUDGET_LIMIT_USD` | `75.0` | Monthly API budget |
| `ring_seconds` | `VOICEFORGE_RING_SECONDS` | `300.0` | Ring buffer duration |
| `ring_file_path` | `VOICEFORGE_RING_FILE_PATH` | auto (`XDG_RUNTIME_DIR`/`~/.cache`) | Ring PCM path |
| `rag_db_path` | `VOICEFORGE_RAG_DB_PATH` | auto (`XDG_DATA_HOME`/`~/.local/share`) | RAG SQLite path |
| `smart_trigger` | `VOICEFORGE_SMART_TRIGGER` | `false` | Auto-analyze mode |
| `monitor_source` | `VOICEFORGE_MONITOR_SOURCE` | `null` | PipeWire monitor source |
| `aggressive_memory` | `VOICEFORGE_AGGRESSIVE_MEMORY` | `false` | Unload models after analyze |
| `pyannote_restart_hours` | `VOICEFORGE_PYANNOTE_RESTART_HOURS` | `2` | Periodic pyannote restart |
| `pipeline_step2_timeout_sec` | `VOICEFORGE_PIPELINE_STEP2_TIMEOUT_SEC` | `25.0` | Timeout for parallel stage |
| `streaming_stt` | `VOICEFORGE_STREAMING_STT` | `false` | Live transcript in listen mode |
| `language` | `VOICEFORGE_LANGUAGE` | `auto` | UI language: `auto/ru/en` |

## Non-VOICEFORGE Environment Inputs

| Variable | Default | Description |
|---|---|---|
| `XDG_CONFIG_HOME` | `~/.config` | Config base path |
| `XDG_DATA_HOME` | `~/.local/share` | Data base path (transcripts/metrics/rag) |
| `XDG_RUNTIME_DIR` | `~/.cache` | Runtime path for ring buffer |
| `VOICEFORGE_SERVICE_FILE` | unset | Override systemd unit file source |
| `VOICEFORGE_IPC_ENVELOPE` | `false` | IPC envelope mode in daemon/dbus |
| `OLLAMA_HOST` | `http://localhost:11434` | Local LLM endpoint |

## Keyring Contract

Service name: `voiceforge`

Supported key names:
- `anthropic`
- `openai`
- `huggingface`

Never pass these keys through git-tracked files.
