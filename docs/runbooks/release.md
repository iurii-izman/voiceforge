# Release Runbook

Version line:
- Python package: `0.1.0a1`
- Git tag format: `v0.1.0-alpha.1`

Pre-release checklist:
1. `./scripts/verify_pr.sh` passes.
2. `uv build` succeeds.
3. Tag and publish release from `main`.
