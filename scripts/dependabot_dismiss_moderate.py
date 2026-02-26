#!/usr/bin/env python3
"""Dismiss Dependabot moderate alert (CVE-2025-69872 / diskcache). Uses keyring voiceforge/github_token.
See docs/runbooks/dependabot-review.md. Usage: uv run python scripts/dependabot_dismiss_moderate.py [--dry-run]
"""

from __future__ import annotations

import json
import sys
import urllib.error
import urllib.request

REPO = "iurii-izman/voiceforge"
API_BASE = "https://api.github.com"
TARGET_CVE = "CVE-2025-69872"
TARGET_PACKAGE = "diskcache"
DISMISS_COMMENT = "No fix version yet. See docs/runbooks/security.md. Revisit when upstream fixes."


def _fetch_open_alerts(headers: dict) -> list:
    url = f"{API_BASE}/repos/{REPO}/dependabot/alerts?state=open"
    req = urllib.request.Request(url, headers=headers)
    with urllib.request.urlopen(req, timeout=30) as resp:
        return json.loads(resp.read().decode())


def _find_target_alert(alerts: list) -> dict | None:
    for a in alerts:
        adv = a.get("security_advisory") or {}
        vuln = a.get("security_vulnerability") or {}
        pkg = (vuln.get("package") or {}).get("name", "")
        cve_id = adv.get("cve_id") or ""
        if cve_id == TARGET_CVE or pkg == TARGET_PACKAGE:
            return a
    return None


def _dismiss_alert(alert_number: int, headers: dict) -> None:
    body = json.dumps({"state": "dismissed", "reason": "risk_accepted", "dismiss_comment": DISMISS_COMMENT}).encode()
    patch_url = f"{API_BASE}/repos/{REPO}/dependabot/alerts/{alert_number}"
    req = urllib.request.Request(patch_url, data=body, headers={**headers, "Content-Type": "application/json"}, method="PATCH")
    with urllib.request.urlopen(req, timeout=30) as resp:
        result = json.loads(resp.read().decode())
    print(f"Dismissed alert #{alert_number}: {result.get('state', 'dismissed')}")


def main() -> None:
    from voiceforge.core.secrets import get_api_key

    token = get_api_key("github_token") or get_api_key("github_token_pat")
    if not token:
        print("github_token / github_token_pat not in keyring (service=voiceforge)", file=sys.stderr)
        sys.exit(1)

    dry_run = "--dry-run" in sys.argv
    headers = {
        "Accept": "application/vnd.github+json",
        "Authorization": f"Bearer {token}",
        "X-GitHub-Api-Version": "2022-11-28",
    }

    try:
        alerts = _fetch_open_alerts(headers)
    except urllib.error.HTTPError as e:
        body = e.read().decode() if e.fp else ""
        print(f"GitHub API error {e.code}: {body[:500]}", file=sys.stderr)
        sys.exit(2)
    except Exception as e:
        print(f"Request failed: {e}", file=sys.stderr)
        sys.exit(2)

    target = _find_target_alert(alerts)
    if not target:
        print("No open Dependabot alert for diskcache / CVE-2025-69872. Already dismissed or fixed.")
        return

    alert_number = target.get("number")
    pkg = (target.get("security_vulnerability") or {}).get("package", {}).get("name", "?")
    cve = (target.get("security_advisory") or {}).get("cve_id") or "?"
    print(f"Found alert #{alert_number}: {pkg} ({cve})")

    if dry_run:
        print("Dry-run: would dismiss with reason=risk_accepted")
        return

    try:
        _dismiss_alert(alert_number, headers)
    except urllib.error.HTTPError as e:
        body_read = e.read().decode() if e.fp else ""
        print(f"Dismiss failed {e.code}: {body_read[:500]}", file=sys.stderr)
        sys.exit(2)


if __name__ == "__main__":
    main()
