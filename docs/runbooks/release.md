# Release Runbook

Version line:
- Python package: `0.1.0a1`
- Git tag format: `v0.1.0-alpha.1`

Pre-release checklist:
1. `./scripts/verify_pr.sh` passes.
2. `./scripts/smoke_clean_env.sh` passes.
3. `uv build --wheel` succeeds.
4. Version and tag line are aligned (`0.1.0a1` / `v0.1.0-alpha.1`).

Release commands:

```bash
./scripts/verify_pr.sh
./scripts/smoke_clean_env.sh
uv build --wheel
git tag -a v0.1.0-alpha.1 -m "voiceforge alpha0.1"
```

Expected outputs:

1. `verify_pr.sh: ALL CHECKS PASSED`
2. `smoke_clean_env.sh: OK`
3. `uv build --wheel` produces `dist/*.whl`
