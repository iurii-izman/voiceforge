#!/usr/bin/env python3
"""Cleanup GitHub open PRs and report Sonar (uses gh CLI if available, else keyring github_token).
Closes PRs not updated in STALE_DAYS and deletes their head branch. Use --dry-run to only list.
Usage: uv run python scripts/cleanup_github_pr_sonar.py [--dry-run] [--days 90]
"""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
from datetime import UTC, datetime, timedelta
from pathlib import Path

STALE_DAYS = 90


def gh(args: list[str], capture: bool = True) -> tuple[int, str]:
    cmd = ["gh", *args]
    r = subprocess.run(cmd, capture_output=capture, text=True, timeout=60)
    out = (r.stdout or "").strip() if capture else ""
    return (r.returncode, out)


def list_open_prs() -> list[dict]:
    code, out = gh(
        ["pr", "list", "--state", "open", "--limit", "100", "--json", "number,title,headRefName,updatedAt,createdAt,url"]
    )
    if code != 0:
        print("gh pr list failed", file=sys.stderr)
        return []
    if not out:
        return []
    return json.loads(out)


def run_sonar_list() -> None:
    repo_root = Path(__file__).resolve().parents[1]
    r = subprocess.run(
        [sys.executable, str(repo_root / "scripts" / "sonar_list_branches.py")],
        cwd=str(repo_root),
        capture_output=True,
        text=True,
        timeout=30,
    )
    if r.returncode == 0 and r.stdout:
        print("\n--- SonarCloud branches ---")
        print(r.stdout.strip())
    else:
        print("\n(Sonar: uv run python scripts/sonar_list_branches.py)")


def main() -> None:
    parser = argparse.ArgumentParser(description="Cleanup stale GitHub PRs and report Sonar")
    parser.add_argument("--dry-run", action="store_true", help="Only list, do not close/delete")
    parser.add_argument("--days", type=int, default=STALE_DAYS, help=f"Stale threshold in days (default {STALE_DAYS})")
    args = parser.parse_args()

    code, _ = gh(["auth", "status"])
    if code != 0:
        print("gh not authenticated; run: gh auth login", file=sys.stderr)
        sys.exit(1)

    prs = list_open_prs()
    print(f"Open PRs: {len(prs)}")

    if not prs:
        run_sonar_list()
        return

    cutoff = datetime.now(UTC) - timedelta(days=args.days)
    closed = 0
    for pr in prs:
        num = pr.get("number")
        title = (pr.get("title") or "")[:50]
        head_ref = (pr.get("headRefName") or "").strip()
        updated = pr.get("updatedAt") or pr.get("createdAt") or ""
        try:
            updated_dt = datetime.fromisoformat(updated.replace("Z", "+00:00"))
        except Exception:
            updated_dt = datetime.now(UTC)
        is_stale = updated_dt.replace(tzinfo=UTC) < cutoff

        print(f"  #{num} {title!r} branch={head_ref} updated={updated[:10]} stale={is_stale}")

        if not is_stale:
            continue
        comment = f"Closed by cleanup: no activity for {args.days}+ days. Branch deleted to reduce Sonar/PR clutter."
        if args.dry_run:
            print(f"    [dry-run] would close and delete {head_ref}")
        else:
            gh(["pr", "close", str(num), "--comment", comment], capture=False)
            # Delete branch (same-repo; may 404 if from fork)
            gh(["api", f"repos/iurii-izman/voiceforge/git/refs/heads/{head_ref}", "-X", "DELETE"], capture=True)
            print(f"    closed #{num} and deleted branch {head_ref}")
        closed += 1

    print(f"\nStale PRs closed: {closed}")
    run_sonar_list()


if __name__ == "__main__":
    main()
