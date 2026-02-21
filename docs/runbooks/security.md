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

Temporary exception:
- `CVE-2025-69872` (`diskcache`) has no published fixed version yet; keep ignore pinned and remove it as soon as upstream ships a fix.
