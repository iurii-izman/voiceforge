#!/usr/bin/env python3
"""List SonarCloud project branches (keyring voiceforge/sonar_token).
Helps see what PR/branch analyses are present. Usage: uv run python scripts/sonar_list_branches.py [--json]
"""

from __future__ import annotations

import json
import sys
import urllib.error
import urllib.parse
import urllib.request

SONAR_PROJECT_KEY = "iurii-izman_voiceforge"
SONAR_API_BASE = "https://sonarcloud.io/api"


def main() -> None:
    from voiceforge.core.secrets import get_api_key

    token = get_api_key("sonar_token")
    if not token:
        print("sonar_token not found in keyring (service=voiceforge)", file=sys.stderr)
        sys.exit(1)

    url = f"{SONAR_API_BASE}/project_branches/list?project={urllib.parse.quote(SONAR_PROJECT_KEY)}"
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

    branches = data.get("branches", [])
    if "--json" in sys.argv:
        print(json.dumps({"branches": branches}, indent=2, ensure_ascii=False))
        return

    if not branches:
        print("No branches in SonarCloud (or API returned empty).")
        return

    print(f"SonarCloud branches ({len(branches)}):")
    for b in branches:
        name = b.get("name", "?")
        is_main = b.get("isMain", False)
        main_str = " [main]" if is_main else ""
        analysis = b.get("analysisDate") or b.get("status", {}).get("qualityGateStatus", "—")
        print(f"  {name}{main_str}  last: {analysis}")


if __name__ == "__main__":
    main()
