# Security Policy

## Supported Versions

VoiceForge is currently maintained on the active `main` branch and the latest pre-release tag.

## Reporting a Vulnerability

Please do **not** open a public issue for undisclosed vulnerabilities.

Use one of the following:

1. GitHub Security Advisory (preferred):
   - Go to `Security` tab of the repository.
   - Create a private vulnerability report.
2. If advisory flow is unavailable, open an issue with label `type:security` **without sensitive details**,
   and state that you can share details privately.

Include:
- affected component/module
- impact and realistic attack scenario
- reproduction steps or proof-of-concept
- suggested remediation (if available)

## Response Targets

- Initial triage response: within 72 hours
- Confirmation and severity classification: within 7 days
- Fix target depends on severity and exploitability

## Security Baseline in This Repository

- Secrets are expected in keyring/secret storage, never in source code.
- CI security gates are blocking (`pip-audit`, `bandit`, `gitleaks`, `semgrep`).
- Local secret scanning is required before push via pre-commit `gitleaks`
  with repository config in `.gitleaks.toml`.
- Semgrep suppressions are allowed only via registry with owner + issue + expiry
  (see `docs/SEMGREP_POLICY.md` and `.github/semgrep_suppressions.json`).
- Temporary CVE exceptions must have owner + expiry + tracking issue
  (see `docs/runbooks/security.md`).
- Sonar quality gate is focused on New Code to prevent legacy noise masking new risks
  (see `docs/runbooks/repo-governance.md` and `docs/runbooks/release.md`).
