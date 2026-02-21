# Bootstrap Runbook

Recommended bootstrap:

```bash
./scripts/bootstrap.sh
```

Manual path:

```bash
uv sync --extra all
uv run pre-commit install --hook-type pre-commit --hook-type pre-push
./scripts/doctor.sh
uv run voiceforge status
./scripts/smoke_clean_env.sh
```

Optional service mode:

```bash
uv run voiceforge install-service
uv run voiceforge daemon
```
