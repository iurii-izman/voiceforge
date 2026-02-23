# Cursor Agent Setup (effective & cheap)

How to configure Cursor so the agent works effectively and cheaply. VoiceForge API keys stay in **keyring**; Cursor-specific settings are below.

## Cloud Agents dashboard

- **Create PRs**: e.g. "For Single Model Runs" — PR only when needed, not every run.
- **Slack Notifications**: optional; turn off if you want fewer distractions and cheaper runs.
- **Repository routing**: add rules only if you use the Slack bot and have multiple repos.
- **User API Keys**: create only if you use Cursor Agent CLI or Cloud Agent API; not required for normal IDE usage.
- **My Secrets**: use only when the agent runs in an environment **without** keyring (e.g. Cloud Agent in a container). Do **not** put VoiceForge API keys here unless that agent run cannot access your keyring. Never commit secret values; see `docs/runbooks/security.md`.

## What to put in My Secrets (optional)

Only if the agent must call VoiceForge-related APIs from a context where keyring is unavailable:

- Variable **names** (no values in repo): `ANTHROPIC_API_KEY`, `OPENAI_API_KEY`, `GEMINI_API_KEY` (LiteLLM), or Huggingface token if pyannote is used by that run.
- Prefer running tasks locally with keyring; use My Secrets for CI/cloud runs when necessary.

## Local development (Fedora Atomic Cosmic)

- API keys: store in keyring on the host or inside toolbox/distrobox:
  ```bash
  keyring set voiceforge anthropic
  keyring set voiceforge openai
  keyring set voiceforge huggingface
  ```
- Bootstrap: `./scripts/bootstrap.sh` then `uv sync --extra all`; verify with `uv run voiceforge status` and `./scripts/doctor.sh`.
- See `docs/runbooks/config-env-contract.md` for all `VOICEFORGE_*` and keyring key names.
