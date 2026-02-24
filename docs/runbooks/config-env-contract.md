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
| `smart_trigger` | `VOICEFORGE_SMART_TRIGGER` | `false` | Auto-analyze mode. **Default policy (roadmap 15):** remains `false` until user feedback on false positives; when enabling by default, update default here and in config source, and note in release. |
| `smart_trigger_template` | `VOICEFORGE_SMART_TRIGGER_TEMPLATE` | `null` | Optional template for smart-trigger analyze (e.g. `standup`, `one_on_one`). Only when `smart_trigger` is true. |
| `monitor_source` | `VOICEFORGE_MONITOR_SOURCE` | `null` | PipeWire monitor source |
| `aggressive_memory` | `VOICEFORGE_AGGRESSIVE_MEMORY` | `false` | Unload models after analyze |
| `pyannote_restart_hours` | `VOICEFORGE_PYANNOTE_RESTART_HOURS` | `2` | Periodic pyannote restart |
| `pipeline_step2_timeout_sec` | `VOICEFORGE_PIPELINE_STEP2_TIMEOUT_SEC` | `25.0` | Timeout for parallel stage |
| `streaming_stt` | `VOICEFORGE_STREAMING_STT` | `false` | Live transcript in listen mode |
| `live_summary_interval_sec` | `VOICEFORGE_LIVE_SUMMARY_INTERVAL_SEC` | `90` | Interval (and window) in seconds for `listen --live-summary` (e.g. every 90s for last 90s) |
| `language` | `VOICEFORGE_LANGUAGE` | `auto` | UI language; when `ru`/`en` also passed to Whisper as STT hint |
| `ollama_model` | `VOICEFORGE_OLLAMA_MODEL` | `phi3:mini` | Ollama model for local classify/simple_answer |
| `pii_mode` | `VOICEFORGE_PII_MODE` | `ON` | PII redaction before LLM: `OFF` (none), `ON` (full regex+GLiNER), `EMAIL_ONLY` (email only) |

**Validation:** Settings validates `model_size` (allowed: tiny, base, small, medium, large-v2, large-v3, large), `sample_rate` (1..192000), `default_llm` (non-empty), `budget_limit_usd` (≥ 0), `pipeline_step2_timeout_sec` (positive), `ollama_model` (non-empty), `ring_seconds` (positive), `pyannote_restart_hours` (≥ 1), `live_summary_interval_sec` (≥ 1). Invalid values raise at load.

## Non-VOICEFORGE Environment Inputs

| Variable | Default | Description |
|---|---|---|
| `XDG_CONFIG_HOME` | `~/.config` | Config base path |
| `XDG_DATA_HOME` | `~/.local/share` | Data base path (transcripts/metrics/rag) |
| `XDG_RUNTIME_DIR` | `~/.cache` | Runtime path for ring buffer |
| `VOICEFORGE_SERVICE_FILE` | unset | Override systemd unit file source |
| `VOICEFORGE_IPC_ENVELOPE` | `true` | IPC envelope mode in daemon/dbus (set to `false` for legacy plain-string clients) |
| `OLLAMA_HOST` | `http://localhost:11434` | Local LLM endpoint |

## D-Bus API (десктоп ↔ демон)

Полный контракт методов и сигналов: **`desktop/DBUS.md`**. При изменении D-Bus интерфейса обновлять `desktop/DBUS.md` и при необходимости этот раздел (например, новые поля в GetSettings).

## D-Bus GetSettings (W4)

Method `GetSettings` returns a JSON object with settings for UI. It includes:
- `model_size`, `default_llm`, `budget_limit_usd`, `smart_trigger`, `sample_rate`, `streaming_stt`, `pii_mode`.
- **`privacy_mode`** — alias for `pii_mode` (same value); kept for UI compatibility. There is no separate Settings field; both keys reflect `pii_mode` / `VOICEFORGE_PII_MODE`.

**CLI** `status` and `status --output json` also include `pii_mode` (and in text output: `status.pii_mode` line) for PII UX (#11).

## Cost (cost_usd) source of truth (W9)

- **metrics.db** (`llm_calls`): source of truth for **totals and reporting**. All LLM calls are logged here with `cost_usd`; `get_stats(days)`, `get_cost_today()`, and D-Bus `GetAnalytics` use this DB.
- **transcripts.db** (`analyses.cost_usd`): **per-session snapshot** of the cost of the analyze call that produced that analysis. Used for session detail and export. Not re-synced if metrics are migrated or recalculated.
- For consistency: prefer metrics.db for dashboards and budgets; use analyses.cost_usd only for “cost of this session”.

## Keyring Contract

Service name: `voiceforge`

**Используются в коде (LiteLLM / pipeline):**
- `anthropic` → ANTHROPIC_API_KEY
- `openai` → OPENAI_API_KEY
- `huggingface` → pyannote/STT
- `google` → GEMINI_API_KEY (опционально)

**Справочник всех ключей в keyring (service=voiceforge)** — для агента и автоматизации; значения только из keyring, не коммитить:
- `anthropic`, `openai`, `huggingface`, `google` — API для LLM/STT
- `sonar_token` — SonarCloud (CI, quality gate)
- `github_token`, `github_token_pat` — GitHub (API, push, PR)
- `codecov_token`, `codecov_token_codecov.yml` — Codecov
- `webhook_telegram`, `b24webhook` — интеграции (Telegram, Bitrix24)
- `MCPcode` — прочие сервисы (не для коммита)

Полный список имён: см. `docs/runbooks/keyring-keys-reference.md`.

Never pass these keys through git-tracked files.
