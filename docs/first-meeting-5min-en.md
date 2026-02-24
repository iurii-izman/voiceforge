# First meeting in 5 minutes (alpha0.1)

Short scenario: record audio → analyze meeting → view history and export.

## 1. Install and check

```bash
./scripts/bootstrap.sh
uv run voiceforge status   # or voiceforge doctor — full environment diagnostics
```

API keys are stored in **keyring** (service `voiceforge`):

```bash
keyring set voiceforge anthropic
keyring set voiceforge openai
keyring set voiceforge huggingface   # if you need pyannote
```

## 2. Recording to ring buffer

In a separate terminal or in the background:

```bash
uv run voiceforge listen
```

Records from the microphone into a ring buffer (default: last 5 minutes). Stop: Ctrl+C.

## 3. Analyze a segment

After the meeting or during a pause:

```bash
uv run voiceforge analyze --seconds 60
```

Processes the last 60 seconds: transcription → diarization → RAG → LLM. Result is printed to the console and written to the session log.

Meeting templates (priority 1):

```bash
uv run voiceforge analyze --template standup
uv run voiceforge analyze --template one_on_one
# standup | sprint_review | one_on_one | brainstorm | interview
```

## 4. History and export

List sessions:

```bash
uv run voiceforge history --last 10
```

Session details and export to file:

```bash
uv run voiceforge history --id 1
uv run voiceforge export --id 1 --format md -o meeting.md
uv run voiceforge export --id 1 --format pdf   # optional: requires pandoc and pdflatex (dnf install pandoc texlive-scheme-basic)
```

## 5. Cost report

LLM costs for a period (from metrics DB):

```bash
uv run voiceforge cost --days 30
uv run voiceforge cost --from 2025-01-01 --to 2025-01-31   # for a date range
uv run voiceforge cost --days 7 --output json
```

## 6. Action items for the next meeting (priority 2)

Update action item statuses from session 1 using the transcript of session 2:

```bash
uv run voiceforge action-items update --from-session 1 --next-session 2
```

Statuses are saved to `~/.local/share/voiceforge/action_item_status.json` (or `XDG_DATA_HOME/voiceforge/`).

## 7. Settings

Config: `~/.config/voiceforge/voiceforge.yaml` or `voiceforge.yaml` in the current directory. Environment variables `VOICEFORGE_*` take precedence.

Main options:

- **ollama_model** — Ollama model for local responses (default `phi3:mini`).
- **language** — STT language: `auto` (from LANG), `ru`, `en`.
- **pii_mode** — PII masking before LLM: `OFF`, `ON`, `EMAIL_ONLY`.
- **streaming_stt** — show partial/final transcript during `listen` (true/false).
- When running `listen` you can use `--live-summary` for periodic short summaries of the last 90 seconds.

See: `docs/runbooks/config-env-contract.md`, feature priorities: `docs/roadmap-priority.md`.
