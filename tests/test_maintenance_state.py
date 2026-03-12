from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from scripts.check_maintenance_state import classify_raw_pip_audit, collect_maintenance_state, summarize_open_issues


def _result(returncode: int, stdout: str = "", stderr: str = "") -> subprocess.CompletedProcess[str]:
    return subprocess.CompletedProcess(args=["cmd"], returncode=returncode, stdout=stdout, stderr=stderr)


def test_classify_raw_pip_audit_waiting_upstream() -> None:
    result = _result(1, stdout="Found CVE-2025-69872 in diskcache")
    report = classify_raw_pip_audit(result, known_wait_state_cves={"CVE-2025-69872"})
    assert report["status"] == "waiting-upstream"
    assert report["cves"] == ["CVE-2025-69872"]


def test_classify_raw_pip_audit_fixed() -> None:
    result = _result(0, stdout="No known vulnerabilities found")
    report = classify_raw_pip_audit(result)
    assert report["status"] == "clean"


def test_classify_raw_pip_audit_unexpected_vulnerabilities() -> None:
    result = _result(1, stdout="Found CVE-2026-12345 in package")
    report = classify_raw_pip_audit(result)
    assert report["status"] == "unexpected-vulnerabilities"
    assert report["cves"] == ["CVE-2026-12345"]


def test_summarize_open_issues_reports_maintenance_mode() -> None:
    result = _result(0, stdout=json.dumps([{"number": 65, "title": "wait state", "url": "x"}]))
    summary = summarize_open_issues(result, allowed_wait_states={65})
    assert summary["status"] == "maintenance-mode"
    assert summary["unexpected_numbers"] == []


def test_summarize_open_issues_reports_new_work() -> None:
    result = _result(
        0,
        stdout=json.dumps([{"number": 65, "title": "wait state", "url": "x"}, {"number": 200, "title": "bug", "url": "y"}]),
    )
    summary = summarize_open_issues(result, allowed_wait_states={65})
    assert summary["status"] == "new-work-present"
    assert summary["unexpected_numbers"] == [200]


def test_collect_maintenance_state_ready_with_known_wait_state(tmp_path: Path) -> None:
    desktop = tmp_path / "desktop"
    src_tauri = desktop / "src-tauri"
    src_tauri.mkdir(parents=True)
    (desktop / "package.json").write_text(
        json.dumps(
            {
                "scripts": {
                    "e2e:native:headless": "bash ../scripts/run_desktop_native_smoke.sh --headless",
                    "e2e:release-gate": "npm run build && npm run e2e:gate",
                }
            }
        ),
        encoding="utf-8",
    )
    (src_tauri / "tauri.conf.json").write_text(
        json.dumps({"plugins": {"updater": {"pubkey": "", "endpoints": []}}}),
        encoding="utf-8",
    )

    def fake_run(args: list[str], *, cwd: Path) -> subprocess.CompletedProcess[str]:
        joined = " ".join(args)
        if "check_docs_consistency.py" in joined:
            return _result(0, stdout="docs-consistency OK")
        if args and args[0].endswith("pip-audit"):
            return _result(0, stdout="No known vulnerabilities found")
        if args[:3] == ["gh", "issue", "list"]:
            return _result(0, stdout=json.dumps([]))
        raise AssertionError(f"unexpected command: {args}")

    report = collect_maintenance_state(
        tmp_path,
        run_command=fake_run,
        which=lambda command: {"pip-audit": "/usr/bin/pip-audit", "gh": "/usr/bin/gh", "npm": "/usr/bin/npm"}.get(command),
    )

    assert report["overall_status"] == "ready"
    assert report["security_recheck"]["raw_audit"]["status"] == "clean"
    assert report["queue_summary"]["status"] == "maintenance-mode"


def test_collect_maintenance_state_requires_attention_when_wait_state_clears(tmp_path: Path) -> None:
    desktop = tmp_path / "desktop"
    src_tauri = desktop / "src-tauri"
    src_tauri.mkdir(parents=True)
    (desktop / "package.json").write_text(
        json.dumps(
            {
                "scripts": {
                    "e2e:native:headless": "bash ../scripts/run_desktop_native_smoke.sh --headless",
                    "e2e:release-gate": "npm run build && npm run e2e:gate",
                }
            }
        ),
        encoding="utf-8",
    )
    (src_tauri / "tauri.conf.json").write_text(
        json.dumps({"plugins": {"updater": {"pubkey": "", "endpoints": []}}}),
        encoding="utf-8",
    )

    def fake_run(args: list[str], *, cwd: Path) -> subprocess.CompletedProcess[str]:
        joined = " ".join(args)
        if "check_docs_consistency.py" in joined:
            return _result(0, stdout="docs-consistency OK")
        if args and args[0].endswith("pip-audit"):
            return _result(1, stdout="Found CVE-2026-12345 in package")
        if args[:3] == ["gh", "issue", "list"]:
            return _result(0, stdout=json.dumps([]))
        raise AssertionError(f"unexpected command: {args}")

    report = collect_maintenance_state(
        tmp_path,
        run_command=fake_run,
        which=lambda command: {"pip-audit": "/usr/bin/pip-audit", "gh": "/usr/bin/gh", "npm": "/usr/bin/npm"}.get(command),
    )

    assert report["overall_status"] == "needs-attention"
    assert report["security_recheck"]["raw_audit"]["status"] == "unexpected-vulnerabilities"
