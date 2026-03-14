#!/usr/bin/env python3
"""
Write updates/update.json for Tauri updater from build artifacts.

Usage (from repo root):
  uv run python scripts/write_update_json.py --version 1.0.0-beta.1 \\
    --url "https://github.com/OWNER/REPO/releases/download/v1.0.0-beta.1/VoiceForge_1.0.0-beta.1_amd64.deb" \\
    --signature-file desktop/src-tauri/target/release/bundle/deb/VoiceForge_1.0.0-beta.1_amd64.deb.sig

Or set env: VERSION, UPDATE_URL, SIGNATURE_FILE (path to .sig file).
Used by release workflow or after local signed build to publish the update manifest.
"""

from __future__ import annotations

import argparse
import json
import os
import sys
from datetime import UTC, datetime
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
UPDATES_JSON = REPO_ROOT / "updates" / "update.json"


def main() -> int:
    ap = argparse.ArgumentParser(description="Write updates/update.json for Tauri updater")
    ap.add_argument("--version", default=None, help="Version (e.g. 1.0.0-beta.1)")
    ap.add_argument("--url", default=None, help="Download URL for linux-x86_64 .deb or AppImage")
    ap.add_argument("--signature-file", type=Path, default=None, help="Path to .sig file")
    ap.add_argument("--notes", default="See CHANGELOG.md", help="Release notes")
    args = ap.parse_args()

    version = args.version or os.environ.get("VERSION", "")
    url = args.url or os.environ.get("UPDATE_URL", "")
    sig_path = args.signature_file or (os.environ.get("SIGNATURE_FILE") and Path(os.environ["SIGNATURE_FILE"]))

    if not version or not url:
        print("Need --version and --url (or env VERSION, UPDATE_URL)", file=sys.stderr)
        return 1

    if sig_path is None:
        print("Need --signature-file or env SIGNATURE_FILE (path to .sig)", file=sys.stderr)
        return 1

    sig_path = Path(sig_path)
    if not sig_path.is_absolute():
        sig_path = REPO_ROOT / sig_path
    if not sig_path.exists():
        print(f"Signature file not found: {sig_path}", file=sys.stderr)
        return 1

    signature = sig_path.read_text(encoding="utf-8").strip()

    payload = {
        "version": version,
        "notes": args.notes,
        "pub_date": datetime.now(UTC).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "platforms": {
            "linux-x86_64": {
                "signature": signature,
                "url": url,
            }
        },
    }

    UPDATES_JSON.parent.mkdir(parents=True, exist_ok=True)
    UPDATES_JSON.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    print(f"Wrote {UPDATES_JSON}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
