# Security Policy

## Supported versions

| Version | Supported          |
|---------|--------------------|
| 0.2.x   | :white_check_mark: |
| < 0.2   | :x:                |

## Reporting a vulnerability

Please do **not** open a public issue for security vulnerabilities.

1. **Preferred:** Open a [private security advisory](https://github.com/iurii-izman/voiceforge/security/advisories/new) in this repository (if you have access).
2. **Alternatively:** Email the maintainer or report via the [Security Incident issue template](.github/ISSUE_TEMPLATE/security-incident.yml) and set severity; we will treat it confidentially.

We will acknowledge receipt and aim to respond within a reasonable time. For accepted issues we will coordinate disclosure and credit as appropriate.

## Security practices in this project

- **Secrets:** No API keys or tokens in the repo; use system keyring (see [keyring-keys-reference](docs/runbooks/keyring-keys-reference.md)).
- **CI:** Gitleaks, Bandit, pip-audit, Semgrep, CodeQL run on push/PR; see [security runbook](docs/runbooks/security.md).
- **Dependencies:** Dependabot and weekly security workflow; known CVE exceptions documented in runbooks until upstream fixes are available.
