#!/usr/bin/env python3
"""One-off credential helper: output github_token_pat from keyring for git push."""

from __future__ import annotations

import sys


def main() -> None:
    # Git credential protocol: key=value lines on stdin
    lines = sys.stdin.read().strip().splitlines()
    env = {k: v for line in lines if "=" in line and not line.startswith("=") for k, v in [line.split("=", 1)]}
    if env.get("host") != "github.com":
        return
    from voiceforge.core.secrets import get_api_key

    token = get_api_key("github_token_pat")
    if token:
        print("username=git", flush=True)
        print("password=" + token, flush=True)


if __name__ == "__main__":
    main()
