# Bootstrap Runbook

Recommended bootstrap:

```bash
./scripts/bootstrap.sh
```

Manual path:

```bash
uv sync --extra all
uv run voiceforge status
./scripts/smoke_clean_env.sh
```

Optional service mode:

```bash
uv run voiceforge install-service
uv run voiceforge daemon
```
