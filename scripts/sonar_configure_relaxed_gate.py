#!/usr/bin/env python3
"""SonarCloud: назначить проекту relaxed quality gate (keyring voiceforge/sonar_token).
Текущий план SonarCloud не позволяет менять gate — скрипт оставлен как справочный; см. repo-governance.md."""

from __future__ import annotations

import json
import sys
import urllib.error
import urllib.request

SONAR_HOST = "https://sonarcloud.io"
ORG = "iurii-izman"
PROJECT_KEY = "iurii-izman_voiceforge"
RELAXED_GATE_NAME = "VoiceForge relaxed"


def get_token() -> str:
    from voiceforge.core.secrets import get_api_key

    token = get_api_key("sonar_token")
    if not token or not token.strip():
        print("sonar_token not found in keyring (service=voiceforge)", file=sys.stderr)
        sys.exit(1)
    return token.strip()


def request(method: str, path: str, token: str) -> dict:
    url = f"{SONAR_HOST}/api/{path}"
    req = urllib.request.Request(url, method=method)
    req.add_header("Authorization", f"Bearer {token}")
    with urllib.request.urlopen(req, timeout=30) as r:
        return json.loads(r.read().decode())


def main() -> None:
    token = get_token()
    gates = request("GET", f"qualitygates/list?organization={ORG}", token)
    quality_gates = gates.get("qualitygates", [])
    target = next((g for g in quality_gates if (g.get("name") or "").strip() == RELAXED_GATE_NAME), None)
    if not target:
        print(f"Gate '{RELAXED_GATE_NAME}' not found. Create it in SonarCloud → Quality Gates.", file=sys.stderr)
        sys.exit(1)
    gate_id = target.get("id")
    select_url = f"{SONAR_HOST}/api/qualitygates/select?organization={ORG}&projectKey={PROJECT_KEY}&gateId={gate_id}"
    req = urllib.request.Request(select_url, method="POST")
    req.add_header("Authorization", f"Bearer {token}")
    try:
        with urllib.request.urlopen(req, timeout=15) as _resp:
            _resp.read()  # consume response (S108: fill block)
        print(f"SonarCloud {PROJECT_KEY} → quality gate: {RELAXED_GATE_NAME} (id={gate_id})")
    except urllib.error.HTTPError as e:
        body = e.read().decode() if e.fp else ""
        if e.code == 403:
            print("API: no permission to set project quality gate (403).", file=sys.stderr)
            print(
                f"Manual: SonarCloud → Project voiceforge → Settings → Quality Gate → select '{RELAXED_GATE_NAME}'",
                file=sys.stderr,
            )
        else:
            print(f"Select failed: {e.code} {body}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
