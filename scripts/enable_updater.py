#!/usr/bin/env python3
"""
Enable Tauri updater: generate signing key (if missing), set pubkey and endpoints in tauri.conf.json.

Run from repo root. Requires Node/npm and desktop deps installed (npm ci in desktop/).
If pubkey is already set, only ensures endpoints and createUpdaterArtifacts.
"""

from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
TAURI_CONF = REPO_ROOT / "desktop" / "src-tauri" / "tauri.conf.json"
DEFAULT_KEY_PATH = Path.home() / ".tauri" / "voiceforge.key"
# Static manifest URL: updated on each release (see docs/runbooks/desktop-updater.md)
DEFAULT_UPDATE_ENDPOINT = "https://raw.githubusercontent.com/iurii-izman/voiceforge/main/updates/update.json"


def _get_repo_url() -> str:
    try:
        r = subprocess.run(
            ["git", "remote", "get-url", "origin"],
            cwd=REPO_ROOT,
            capture_output=True,
            text=True,
            timeout=5,
        )
        if r.returncode == 0 and r.stdout.strip():
            url = r.stdout.strip()
            if url.startswith("git@"):
                url = url.replace("git@github.com:", "https://github.com/").replace(".git", "")
            elif url.endswith(".git"):
                url = url[:-4]
            return url
    except Exception:
        pass
    return "https://github.com/iurii-izman/voiceforge"


def _update_endpoint_from_repo() -> str:
    base = _get_repo_url()
    if "github.com" in base:
        # raw URL for main branch
        base = base.replace("github.com", "raw.githubusercontent.com")
        return f"{base}/main/updates/update.json"
    return DEFAULT_UPDATE_ENDPOINT


def main() -> int:
    if not TAURI_CONF.exists():
        print(f"Not found: {TAURI_CONF}", file=sys.stderr)
        return 1

    data = json.loads(TAURI_CONF.read_text(encoding="utf-8"))
    bundle = data.setdefault("bundle", {})
    plugins = data.setdefault("plugins", {})
    updater = plugins.setdefault("updater", {})

    pubkey = (updater.get("pubkey") or "").strip()
    endpoint = _update_endpoint_from_repo()

    if pubkey:
        updater["endpoints"] = [endpoint]
        bundle["createUpdaterArtifacts"] = True
        TAURI_CONF.write_text(json.dumps(data, indent=2) + "\n", encoding="utf-8")
        print("Updater already had pubkey; set endpoints and createUpdaterArtifacts.")
        return 0

    key_path = Path(os.environ.get("TAURI_SIGNING_KEY_PATH", str(DEFAULT_KEY_PATH)))
    key_path = key_path.resolve()
    key_dir = key_path.parent
    key_dir.mkdir(parents=True, exist_ok=True)

    if key_path.exists():
        pub_path = Path(str(key_path) + ".pub")
        if not pub_path.exists():
            print(
                f"Private key exists at {key_path} but no .pub file. "
                "Run: cd desktop && npm run tauri signer generate -- -w " + str(key_path),
                file=sys.stderr,
            )
            return 1
        pubkey = pub_path.read_text(encoding="utf-8").strip()
    else:
        print("Generating Tauri signing key (one-time)...")
        try:
            subprocess.run(
                ["npm", "run", "tauri", "signer", "generate", "--", "-w", str(key_path)],
                cwd=REPO_ROOT / "desktop",
                check=True,
                capture_output=False,
            )
        except subprocess.CalledProcessError as e:
            print(f"Key generation failed: {e}", file=sys.stderr)
            return 1
        pub_path = Path(str(key_path) + ".pub")
        if not pub_path.exists():
            print("Key generated but .pub file not found.", file=sys.stderr)
            return 1
        pubkey = pub_path.read_text(encoding="utf-8").strip()
        print(f"Key saved: {key_path} and {pub_path}")
        print("  → Back up the private key; add TAURI_SIGNING_PRIVATE_KEY to GitHub Secrets for CI.")

    updater["pubkey"] = pubkey
    updater["endpoints"] = [endpoint]
    bundle["createUpdaterArtifacts"] = True
    TAURI_CONF.write_text(json.dumps(data, indent=2) + "\n", encoding="utf-8")
    print("tauri.conf.json updated: pubkey and endpoints set.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
