# GitHub configuration

- **workflows/** — CI (test, codeql, sonar, gitleaks, semgrep), security-weekly, release, release-draft
- **ISSUE_TEMPLATE/** — Bug, Feature, Security incident, Release regression; config.yml = chooser
- **pull_request_template.md** — PR checklist (Conventional Commits, DoD)
- **CODEOWNERS** — ownership for core, workflows, scripts
- **dependabot.yml** — pip, github-actions, npm (desktop); weekly groups
- **release-drafter.yml** — draft release notes from PR labels
- **rulesets/main-protection.json** — branch rules for main (required checks, linear history)
