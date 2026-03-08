#!/usr/bin/env python3
"""Report the current release-proof path beyond metadata consistency."""

from __future__ import annotations

import argparse
import json
import shutil
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent


def _load_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def classify_updater_state(tauri_conf: dict) -> tuple[str, str]:
    updater = tauri_conf.get("plugins", {}).get("updater") or {}
    pubkey = (updater.get("pubkey") or "").strip()
    endpoints = updater.get("endpoints") or []
    has_pubkey = bool(pubkey)
    has_endpoints = isinstance(endpoints, list) and bool(endpoints)
    if has_pubkey and has_endpoints:
        return "ready", "pubkey and endpoints are configured"
    if not has_pubkey and not has_endpoints:
        return "disabled", "pubkey and endpoints are empty"
    if has_pubkey:
        return "invalid", "pubkey is set but endpoints are empty"
    return "invalid", "endpoints are set but pubkey is empty"


def collect_release_proof_report(
    repo_root: Path = REPO_ROOT,
    which: callable | None = None,
) -> dict:
    command_lookup = which or shutil.which
    tauri_conf = _load_json(repo_root / "desktop/src-tauri/tauri.conf.json")
    package_json = _load_json(repo_root / "desktop/package.json")
    updater_state, updater_detail = classify_updater_state(tauri_conf)
    native_script_present = "e2e:native" in package_json.get("scripts", {})

    cargo_available = bool(command_lookup("cargo"))
    cargo_audit_available = bool(command_lookup("cargo-audit"))
    npm_available = bool(command_lookup("npm"))

    advisory_status = "ready" if cargo_audit_available else "missing-tool"
    advisory_detail = (
        "cargo-audit is available locally"
        if cargo_audit_available
        else "install with `cargo install cargo-audit` or rely on CI job `desktop-audit`"
    )

    native_status = "ready" if native_script_present else "missing-script"
    native_detail = (
        "desktop/package.json defines `e2e:native`"
        if native_script_present
        else "desktop/package.json is missing `e2e:native`"
    )

    if updater_state == "disabled":
        manual_items = [
            {
                "name": "updater_disabled_boundary",
                "status": "manual-not-required",
                "detail": "signed updater proof is not required while updater stays disabled in repo",
            }
        ]
    elif updater_state == "ready":
        manual_items = [
            {
                "name": "signed_updater_release",
                "status": "manual-required",
                "detail": "build signed artifacts and verify update endpoint/install flow",
            }
        ]
    else:
        manual_items = [
            {
                "name": "updater_contract",
                "status": "invalid",
                "detail": updater_detail,
            }
        ]

    return {
        "blocking": [
            {
                "name": "release_metadata",
                "status": "ready",
                "command": "uv run python scripts/check_release_metadata.py",
                "detail": "packaging versions and updater contract",
            }
        ],
        "advisory": [
            {
                "name": "desktop_npm_audit",
                "status": "ready" if npm_available else "missing-tool",
                "command": "cd desktop && npm audit --audit-level=high",
                "detail": "advisory dependency scan used by CI job `desktop-audit`",
            },
            {
                "name": "desktop_cargo_audit",
                "status": advisory_status if cargo_available else "missing-tool",
                "command": "cargo install cargo-audit && cd desktop/src-tauri && cargo audit",
                "detail": advisory_detail if cargo_available else "cargo is not available locally",
            },
        ],
        "native_gate": {
            "name": "desktop_native_smoke",
            "status": native_status,
            "command": "cd desktop && npm run e2e:native",
            "detail": native_detail,
        },
        "updater": {
            "state": updater_state,
            "detail": updater_detail,
            "evidence": "desktop/src-tauri/tauri.conf.json -> plugins.updater",
        },
        "manual": manual_items,
    }


def _print_text_report(report: dict) -> None:
    print("release proof report")
    print("")
    print("blocking")
    for item in report["blocking"]:
        print(f"- {item['name']}: {item['status']}")
        print(f"  command: {item['command']}")
        print(f"  detail: {item['detail']}")
    print("")
    print("advisory")
    for item in report["advisory"]:
        print(f"- {item['name']}: {item['status']}")
        print(f"  command: {item['command']}")
        print(f"  detail: {item['detail']}")
    print("")
    native = report["native_gate"]
    print("local native gate")
    print(f"- {native['name']}: {native['status']}")
    print(f"  command: {native['command']}")
    print(f"  detail: {native['detail']}")
    print("")
    updater = report["updater"]
    print("updater")
    print(f"- state: {updater['state']}")
    print(f"  detail: {updater['detail']}")
    print(f"  evidence: {updater['evidence']}")
    print("")
    print("manual boundary")
    for item in report["manual"]:
        print(f"- {item['name']}: {item['status']}")
        print(f"  detail: {item['detail']}")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--json", action="store_true", dest="as_json")
    args = parser.parse_args(argv)

    report = collect_release_proof_report()
    if args.as_json:
        print(json.dumps(report, indent=2, sort_keys=True))
    else:
        _print_text_report(report)

    if report["updater"]["state"] == "invalid" or report["native_gate"]["status"] == "missing-script":
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
