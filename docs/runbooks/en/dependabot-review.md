# Dependabot: reviewing and closing alerts

Single source: **GitHub → Repository → Security → Dependabot alerts**.

## Steps

1. Open [Dependabot alerts](https://github.com/iurii-izman/voiceforge/security/dependabot) (or repo → Security → Dependabot).
2. For each alert (e.g. 1 moderate):
   - **Accept:** open the suggested PR (Dependabot creates a PR with the dependency update), run tests, merge.
   - **Dismiss:** Dismiss alert with a comment (e.g. "False positive", "Accept risk until next quarter").
3. After resolving, update this runbook or next-iteration-focus: "Dependabot: closed (date)" or "dismissed until …".

## Current status

- **Historical CVE-2025-69872 (diskcache):** the local wait-state is cleared as of 2026-03-13; `uv run pip-audit --desc` is clean again. If the remote Dependabot alert still exists, close it as fixed/obsolete and sync [security-decision-log.md](../security-decision-log.md).
