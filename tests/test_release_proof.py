from __future__ import annotations

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from scripts.check_release_proof import classify_updater_state, collect_release_proof_report


def test_classify_updater_state_disabled() -> None:
    state, detail = classify_updater_state({"plugins": {"updater": {"pubkey": "", "endpoints": []}}})
    assert state == "disabled"
    assert "empty" in detail


def test_classify_updater_state_ready() -> None:
    state, detail = classify_updater_state(
        {
            "plugins": {
                "updater": {
                    "pubkey": "pubkey",
                    "endpoints": ["https://example.com/updates/{{target}}/{{arch}}/{{current_version}}"],
                }
            }
        }
    )
    assert state == "ready"
    assert "configured" in detail


def test_classify_updater_state_invalid() -> None:
    state, detail = classify_updater_state({"plugins": {"updater": {"pubkey": "pubkey", "endpoints": []}}})
    assert state == "invalid"
    assert "endpoints" in detail


def test_release_proof_report_marks_missing_cargo_audit_as_advisory_only(tmp_path: Path) -> None:
    desktop = tmp_path / "desktop"
    src_tauri = desktop / "src-tauri"
    src_tauri.mkdir(parents=True)
    (desktop / "package.json").write_text(
        json.dumps({"scripts": {"e2e:native": "npm --prefix e2e-native run test"}}),
        encoding="utf-8",
    )
    (src_tauri / "tauri.conf.json").write_text(
        json.dumps({"plugins": {"updater": {"pubkey": "", "endpoints": []}}}),
        encoding="utf-8",
    )

    report = collect_release_proof_report(
        tmp_path,
        which=lambda command: {"cargo": "/usr/bin/cargo", "npm": "/usr/bin/npm"}.get(command),
    )

    assert report["updater"]["state"] == "disabled"
    assert report["native_gate"]["status"] == "ready"
    assert report["advisory"][1]["status"] == "missing-tool"
    assert "cargo install cargo-audit" in report["advisory"][1]["detail"]
    assert report["manual"][0]["status"] == "manual-not-required"


def test_release_proof_report_requires_manual_updater_when_ready(tmp_path: Path) -> None:
    desktop = tmp_path / "desktop"
    src_tauri = desktop / "src-tauri"
    src_tauri.mkdir(parents=True)
    (desktop / "package.json").write_text(
        json.dumps({"scripts": {"e2e:native": "npm --prefix e2e-native run test"}}),
        encoding="utf-8",
    )
    (src_tauri / "tauri.conf.json").write_text(
        json.dumps(
            {
                "plugins": {
                    "updater": {
                        "pubkey": "pubkey",
                        "endpoints": ["https://example.com/updates/{{target}}/{{arch}}/{{current_version}}"],
                    }
                }
            }
        ),
        encoding="utf-8",
    )

    report = collect_release_proof_report(
        tmp_path,
        which=lambda command: {"cargo": "/usr/bin/cargo", "cargo-audit": "/usr/bin/cargo-audit", "npm": "/usr/bin/npm"}.get(command),
    )

    assert report["updater"]["state"] == "ready"
    assert report["advisory"][1]["status"] == "ready"
    assert report["manual"][0]["status"] == "manual-required"
