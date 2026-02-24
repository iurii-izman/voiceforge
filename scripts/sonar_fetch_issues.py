#!/usr/bin/env python3
"""Fetch SonarCloud issues for the project (keyring voiceforge/sonar_token).
Output: JSON to stdout or human-readable lines. Usage: uv run python scripts/sonar_fetch_issues.py [--json]
"""

from __future__ import annotations

import json
import sys
import urllib.parse
import urllib.request

# Project key from sonar-project.properties
SONAR_PROJECT_KEY = "iurii-izman_voiceforge"
SONAR_API_BASE = "https://sonarcloud.io/api"


def main() -> None:
    from voiceforge.core.secrets import get_api_key

    token = get_api_key("sonar_token")
    if not token:
        print("sonar_token not found in keyring (service=voiceforge)", file=sys.stderr)
        sys.exit(1)

    url = f"{SONAR_API_BASE}/issues/search?projectKeys={urllib.parse.quote(SONAR_PROJECT_KEY)}&statuses=OPEN,CONFIRMED&ps=500"
    req = urllib.request.Request(url, headers={"Authorization": f"Bearer {token}"})
    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            data = json.loads(resp.read().decode())
    except urllib.error.HTTPError as e:
        body = e.read().decode() if e.fp else ""
        print(f"SonarCloud API error {e.code}: {body[:500]}", file=sys.stderr)
        sys.exit(2)
    except Exception as e:
        print(f"Request failed: {e}", file=sys.stderr)
        sys.exit(2)

    issues = data.get("issues", [])
    total = data.get("total", 0)
    if total > len(issues):
        print(f"Note: total issues {total}, returned {len(issues)} (cap 500)", file=sys.stderr)

    if "--json" in sys.argv:
        print(json.dumps({"total": total, "issues": issues}, indent=2, ensure_ascii=False))
        return

    for i in issues:
        comp = i.get("component", "").split(":")[-1] if i.get("component") else "?"
        line = i.get("line", "")
        rule = i.get("rule", "").split(":")[-1] if i.get("rule") else "?"
        sev = i.get("severity", "?")
        msg = (i.get("message") or "").replace("\n", " ")
        print(f"{comp}:{line} [{sev}] {rule} | {msg}")


if __name__ == "__main__":
    main()
