# Quick start — first meeting in 5 minutes

Linear scenario for alpha testers. Full version: [../../en/first-meeting-5min.md](../../en/first-meeting-5min.md).

## Steps

1. **Dependencies and keys**
   - `./scripts/bootstrap.sh` → `uv sync --extra all`
   - Check: `uv run voiceforge status` or `uv run voiceforge status --doctor`
   - Keys in keyring: `keyring set voiceforge anthropic`, `openai`, `huggingface` (see [config-env-contract.md](config-env-contract.md))

2. **Recording**
   - `uv run voiceforge listen` — record to ring buffer (last 5 min). Stop: Ctrl+C.

3. **Analysis**
   - `uv run voiceforge analyze --seconds 60` — process last 60 s (STT → diarization → RAG → LLM)
   - Templates: `--template standup | one_on_one | sprint_review | brainstorm | interview`

4. **History and export**
   - `uv run voiceforge history --last 10` — list sessions
   - `uv run voiceforge history --id N` — session details; `--output md` — Markdown to stdout
   - `uv run voiceforge history --search "text"` — search in transcripts
   - `uv run voiceforge history --date 2026-02-23` or `--from YYYY-MM-DD --to YYYY-MM-DD`
   - `uv run voiceforge export --id N --format md` — export to Markdown (always available)
   - `uv run voiceforge export --id N --format pdf` — export to PDF **optional**: requires `pandoc` and `pdflatex` (e.g. `dnf install pandoc texlive-scheme-basic`). Without them a hint is shown and Markdown is saved to a temp file.

5. **Costs and diagnostics**
   - `uv run voiceforge cost --days 30` — cost report
   - `uv run voiceforge status --detailed` — breakdown by models/days and % of budget
   - `uv run voiceforge status --doctor` — environment check

6. **Desktop (Tauri)**
   - Build: see [desktop-build-deps.md](desktop-build-deps.md); from repo root `./scripts/check-desktop-deps.sh`, then `cd desktop && npm install && npm run tauri dev`.
   - Before starting the desktop app, start the daemon: `voiceforge daemon` (in a separate terminal or as a service).

7. **Next steps**
   - Action items: `uv run voiceforge action-items update --from-session 1 --next-session 2`
   - Config and env: [config-env-contract.md](config-env-contract.md)
   - Feature priorities: [../roadmap-priority.md](../roadmap-priority.md)
