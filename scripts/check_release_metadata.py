#!/usr/bin/env python3
"""Check release/install metadata consistency for the active VoiceForge alpha line."""

from __future__ import annotations

import json
import re
import sys
import tomllib
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parent.parent


def _load_toml(path: Path) -> dict:
    return tomllib.loads(path.read_text(encoding="utf-8"))


def _pep440_to_desktop_version(version: str) -> str:
    match = re.fullmatch(r"(\d+\.\d+\.\d+)([abrc]+)(\d+)", version)
    if not match:
        raise ValueError(f"Unsupported Python package version format: {version}")
    base, prerelease, number = match.groups()
    prerelease_map = {"a": "alpha", "b": "beta", "rc": "rc"}
    if prerelease not in prerelease_map:
        raise ValueError(f"Unsupported prerelease marker: {prerelease}")
    return f"{base}-{prerelease_map[prerelease]}.{number}"


def collect_release_metadata_errors(repo_root: Path = REPO_ROOT) -> list[str]:
    pyproject = _load_toml(repo_root / "pyproject.toml")
    python_version = pyproject["project"]["version"]
    desktop_version = _pep440_to_desktop_version(python_version)
    expected_tag = f"v{desktop_version}"
    expected_deb_name = f"VoiceForge_{desktop_version}_amd64.deb"

    package_json = json.loads((repo_root / "desktop/package.json").read_text(encoding="utf-8"))
    tauri_conf = json.loads((repo_root / "desktop/src-tauri/tauri.conf.json").read_text(encoding="utf-8"))
    cargo_toml = _load_toml(repo_root / "desktop/src-tauri/Cargo.toml")
    flatpak_manifest = (repo_root / "desktop/flatpak/com.voiceforge.app.yaml").read_text(encoding="utf-8")

    errors: list[str] = []
    all_extra = pyproject["project"]["optional-dependencies"]["all"]
    if "voiceforge[rag,llm,pii,calendar,otel,web-async]" not in all_extra:
        errors.append("pyproject.toml: optional-dependencies.all must include web-async for full-stack install")

    if package_json["version"] != desktop_version:
        errors.append(f"desktop/package.json: expected {desktop_version}, got {package_json['version']}")
    if tauri_conf["version"] != desktop_version:
        errors.append(f"desktop/src-tauri/tauri.conf.json: expected {desktop_version}, got {tauri_conf['version']}")
    cargo_version = cargo_toml["package"]["version"]
    if cargo_version != desktop_version:
        errors.append(f"desktop/src-tauri/Cargo.toml: expected {desktop_version}, got {cargo_version}")

    if expected_tag not in flatpak_manifest:
        errors.append(f"desktop/flatpak/com.voiceforge.app.yaml: expected release tag {expected_tag}")
    if expected_deb_name not in flatpak_manifest:
        errors.append(f"desktop/flatpak/com.voiceforge.app.yaml: expected deb name {expected_deb_name}")

    return errors


def main() -> int:
    errors = collect_release_metadata_errors()
    if errors:
        for error in errors:
            print(error, file=sys.stderr)
        return 1
    print("release metadata OK")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
