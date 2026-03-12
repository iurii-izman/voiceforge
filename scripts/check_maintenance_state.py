#!/usr/bin/env python3
"""Report repo maintenance state after the active engineering queue is complete."""

from __future__ import annotations

import argparse
import json
import re
import shutil
import subprocess
import sys
from pathlib import Path

try:
    from check_release_proof import collect_release_proof_report
except ModuleNotFoundError:
    from scripts.check_release_proof import collect_release_proof_report

REPO_ROOT = Path(__file__).resolve().parent.parent
KNOWN_WAIT_STATE_CVES: set[str] = set()
PIP_AUDIT_CMD = ["pip-audit", "--desc"]


def _run_command(args: list[str], *, cwd: Path = REPO_ROOT) -> subprocess.CompletedProcess[str]:
    return subprocess.run(args, cwd=cwd, capture_output=True, text=True, check=False)


def _status_from_return_code(result: subprocess.CompletedProcess[str]) -> str:
    return "ready" if result.returncode == 0 else "failed"


def _extract_cves(text: str) -> set[str]:
    return set(re.findall(r"CVE-\d{4}-\d+", text))


def _resolve_command(command: str, which: callable) -> list[str]:
    resolved = which(command)
    return [resolved] if resolved else [command]


def classify_raw_pip_audit(
    result: subprocess.CompletedProcess[str],
    *,
    known_wait_state_cves: set[str] = KNOWN_WAIT_STATE_CVES,
) -> dict[str, object]:
    combined = "\n".join(part for part in [result.stdout, result.stderr] if part)
    detected_cves = _extract_cves(combined)

    if result.returncode == 0:
        return {
            "status": "clean",
            "detail": "pip-audit passes without ignore",
            "cves": sorted(detected_cves),
        }

    if known_wait_state_cves and detected_cves and detected_cves.issubset(known_wait_state_cves):
        return {
            "status": "waiting-upstream",
            "detail": "raw pip-audit still fails only on the documented wait-state CVE(s)",
            "cves": sorted(detected_cves),
        }

    return {
        "status": "unexpected-vulnerabilities",
        "detail": "raw pip-audit reports CVEs beyond the documented wait-state",
        "cves": sorted(detected_cves),
    }


def summarize_open_issues(
    result: subprocess.CompletedProcess[str] | None,
    *,
    allowed_wait_states: set[int] | None = None,
) -> dict[str, object]:
    expected_wait_states = allowed_wait_states or set()
    if result is None:
        return {
            "status": "skipped",
            "detail": "GitHub CLI not available; open-issue summary skipped",
            "open_numbers": [],
            "unexpected_numbers": [],
        }

    if result.returncode != 0:
        detail = (result.stderr or result.stdout or "gh issue list failed").strip()
        return {
            "status": "skipped",
            "detail": detail,
            "open_numbers": [],
            "unexpected_numbers": [],
        }

    issues = json.loads(result.stdout)
    open_numbers = sorted(issue["number"] for issue in issues)
    unexpected_numbers = sorted(number for number in open_numbers if number not in expected_wait_states)
    if unexpected_numbers:
        detail = f"open issues beyond maintenance wait-state: {unexpected_numbers}"
        status = "new-work-present"
    elif open_numbers:
        detail = "only documented external wait-state issues remain open"
        status = "maintenance-mode"
    else:
        detail = "no active issues remain open"
        status = "maintenance-mode"
    return {
        "status": status,
        "detail": detail,
        "open_numbers": open_numbers,
        "unexpected_numbers": unexpected_numbers,
    }


def collect_maintenance_state(
    repo_root: Path = REPO_ROOT,
    *,
    run_command: callable = _run_command,
    which: callable | None = None,
) -> dict[str, object]:
    command_lookup = which or shutil.which
    release_proof = collect_release_proof_report(repo_root, which=command_lookup)

    docs_result = run_command([sys.executable, "scripts/check_docs_consistency.py"], cwd=repo_root)
    pip_audit_raw = run_command([*_resolve_command("pip-audit", command_lookup), "--desc"], cwd=repo_root)

    gh_result: subprocess.CompletedProcess[str] | None
    if command_lookup("gh"):
        gh_result = run_command(
            ["gh", "issue", "list", "--state", "open", "--limit", "200", "--json", "number,title,url"],
            cwd=repo_root,
        )
    else:
        gh_result = None

    security_raw = classify_raw_pip_audit(pip_audit_raw)
    queue_summary = summarize_open_issues(gh_result)

    blocking_ready = all(item["status"] == "ready" for item in release_proof["blocking"])
    release_status = "ready" if blocking_ready and release_proof["updater"]["state"] != "invalid" else "needs-attention"
    docs_status = _status_from_return_code(docs_result)
    overall_status = "ready"
    if release_status != "ready" or docs_status != "ready":
        overall_status = "needs-attention"
    if security_raw["status"] != "clean":
        overall_status = "needs-attention"

    return {
        "overall_status": overall_status,
        "release_proof": {
            "status": release_status,
            "blocking": release_proof["blocking"],
            "native_gate": release_proof["native_gate"],
            "updater": release_proof["updater"],
        },
        "docs_consistency": {
            "status": docs_status,
            "detail": "docs consistency is green"
            if docs_status == "ready"
            else (docs_result.stderr or docs_result.stdout).strip(),
        },
        "security_recheck": {
            "raw_audit": security_raw,
            "wait_state_issue": None,
        },
        "queue_summary": queue_summary,
    }


def _print_text_report(report: dict[str, object]) -> None:
    print("maintenance state")
    print("")
    print(f"overall: {report['overall_status']}")
    print("")
    release = report["release_proof"]
    print(f"release-proof: {release['status']}")
    for item in release["blocking"]:
        print(f"- blocking/{item['name']}: {item['status']}")
    print(f"- native/{release['native_gate']['name']}: {release['native_gate']['status']}")
    print(f"- updater: {release['updater']['state']}")
    print("")
    docs = report["docs_consistency"]
    print(f"docs-consistency: {docs['status']}")
    print(f"  detail: {docs['detail']}")
    print("")
    security = report["security_recheck"]
    print(f"pip-audit(raw): {security['raw_audit']['status']}")
    print(f"  detail: {security['raw_audit']['detail']}")
    if security["raw_audit"]["cves"]:
        print(f"  cves: {', '.join(security['raw_audit']['cves'])}")
    print("")
    queue = report["queue_summary"]
    print(f"queue: {queue['status']}")
    print(f"  detail: {queue['detail']}")
    if queue["open_numbers"]:
        print(f"  open issues: {queue['open_numbers']}")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--json", action="store_true", dest="as_json")
    args = parser.parse_args(argv)

    report = collect_maintenance_state()
    if args.as_json:
        print(json.dumps(report, indent=2, sort_keys=True))
    else:
        _print_text_report(report)

    return 0 if report["overall_status"] == "ready" else 1


if __name__ == "__main__":
    raise SystemExit(main())
