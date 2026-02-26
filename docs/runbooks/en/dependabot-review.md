# Dependabot: reviewing and closing alerts

Single source: **GitHub → Repository → Security → Dependabot alerts**.

## Steps

1. Open [Dependabot alerts](https://github.com/iurii-izman/voiceforge/security/dependabot) (or repo → Security → Dependabot).
2. For each alert (e.g. 1 moderate):
   - **Accept:** open the suggested PR (Dependabot creates a PR with the dependency update), run tests, merge.
   - **Dismiss:** Dismiss alert with a comment (e.g. "False positive", "Accept risk until next quarter").
3. After resolving, update this runbook or next-iteration-focus: "Dependabot: closed (date)" or "dismissed until …".

## Current status

- **CVE-2025-69872 (diskcache):** no fix version available (transitive dependency, pulled via litellm). CI already uses `pip-audit --ignore-vuln CVE-2025-69872` (see [security.md](security.md)). Recommended: **dismiss the alert manually**: Dependabot → Alert → Dismiss → "Accept risk", comment: "No fix version yet. See docs/runbooks/security.md. Revisit when upstream fixes." After an upstream fix appears, remove the ignore in security.md and update the dependency.
