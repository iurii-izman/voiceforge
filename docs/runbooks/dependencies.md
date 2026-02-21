# Dependency Policy (alpha0.1)

## Source of truth

1. `pyproject.toml` defines dependency intent.
2. `uv.lock` is the pinned, reproducible source of installed versions.
3. Runtime and CI must use `uv sync --extra all` unless explicitly scoped.

## Update policy

1. Default mode: no ad-hoc upgrades.
2. Updates are performed only through:
   - `./scripts/update_deps.sh`
3. Every dependency update must pass:
   - `./scripts/verify_pr.sh`
   - `./scripts/smoke_clean_env.sh`

## Security exceptions

Temporary pinned exception:
- `CVE-2025-69872` (`diskcache`) has no fix version yet.
- Keep explicit ignore in scripts/workflows until fix is published.

## Lockfile rules

1. Never hand-edit `uv.lock`.
2. Any dependency change in `pyproject.toml` requires regenerating `uv.lock`.
3. Commit `pyproject.toml` and `uv.lock` together.
