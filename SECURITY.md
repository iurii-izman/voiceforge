# Security Policy

## Supported versions

| Version   | Supported          |
| --------- | ------------------ |
| 1.0.x     | :white_check_mark: |
| 0.2.x     | :white_check_mark: |
| &lt; 0.2   | :x:                |

## Reporting a vulnerability

**Do not open a public issue for security vulnerabilities.**

1. **Preferred:** [Open a private security advisory](https://github.com/iurii-izman/voiceforge/security/advisories/new) in this repository (if you have access).
2. **Alternatively:** Use the [Security Incident issue template](.github/ISSUE_TEMPLATE/security-incident.yml) and set severity; we will treat it confidentially. You can also contact the maintainer directly.

We will acknowledge receipt and aim to respond within a reasonable time. For accepted issues we will coordinate disclosure and credit as appropriate.

## Security practices in this project

- **Secrets:** No API keys or tokens in the repo. Use the system keyring; see [keyring-keys-reference](docs/runbooks/keyring-keys-reference.md).
- **CI:** Gitleaks, Bandit, pip-audit, Semgrep, CodeQL run on push/PR.
- **Dependencies:** Dependabot and weekly security workflow. Known exceptions and accepted risks are documented in [security-decision-log](docs/runbooks/security-decision-log.md) and [security-and-dependencies](docs/runbooks/security-and-dependencies.md).
