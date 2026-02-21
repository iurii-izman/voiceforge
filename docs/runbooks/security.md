# Security Runbook

Secrets policy:
- Use keyring only.
- Never commit credentials to git.

Local checks:

```bash
gitleaks detect --source . --config .gitleaks.toml
uv run bandit -r src -ll -q --configfile .bandit.yaml
uv run pip-audit --desc --ignore-vuln CVE-2025-69872
```

If `gitleaks` binary is not installed locally, `scripts/verify_pr.sh` runs the same scan through Podman or Docker.

Temporary exception:
- `CVE-2025-69872` (`diskcache`) has no published fixed version yet; keep ignore pinned and remove it as soon as upstream ships a fix.

Token/keyring rotation policy (minimum):
1. Rotate tokens every 90 days.
2. Keep least privilege scopes only.
3. Remove stale credentials after provider/project changes.
4. Record rotation date and owner in internal audit log.
