#!/usr/bin/env python3
"""Validate documentation links, required stubs, and source-of-truth references."""

from __future__ import annotations

import re
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
MARKDOWN_SUFFIXES = {".md", ".mdc"}
LINK_RE = re.compile(r"(?<!\!)\[[^\]]+\]\(([^)]+)\)")

REQUIRED_FILES = [
    Path("docs/roadmap-priority.md"),
    Path("docs/PROJECT_AUDIT_AND_ROADMAP.md"),
    Path("docs/development-plan-post-audit-2026.md"),
    Path("docs/desktop-tauri-implementation-plan.md"),
    Path("docs/plans/backlog-and-actions.md"),
    Path("docs/plans/roadmap-100-blocks.md"),
    Path("docs/plans/video-meetings-integration.md"),
    Path("docs/plans/desktop-gui-phase2-10-blocks.md"),
    Path("docs/runbooks/voiceforge-cursor-tz.md"),
    Path("docs/runbooks/claude-proposal-alignment.md"),
    Path("docs/runbooks/sonar-pr-cleanup.md"),
    Path("docs/runbooks/alpha0.1-dod.md"),
    Path("docs/runbooks/alpha2-checklist.md"),
    Path("docs/runbooks/rollback-alpha-release.md"),
]

REQUIRED_REFERENCES = {
    Path("AGENTS.md"): [
        "docs/runbooks/agent-context.md",
        "docs/runbooks/next-iteration-focus.md",
        "docs/runbooks/phase-e-decision-log.md",
        "docs/DOCS-INDEX.md",
    ],
    Path("docs/runbooks/agent-context.md"): [
        "next-iteration-focus.md",
        "PROJECT-STATUS-SUMMARY.md",
        "planning.md",
        "ai-tooling-setup.md",
    ],
    Path("docs/runbooks/next-iteration-focus.md"): [
        "phase-e-decision-log.md",
        "PROJECT-STATUS-SUMMARY.md",
    ],
    Path("docs/runbooks/PROJECT-STATUS-SUMMARY.md"): [
        "phase-e-decision-log.md",
        "next-iteration-focus.md",
    ],
    Path("docs/runbooks/planning.md"): [
        "phase-e-decision-log.md",
        "PROJECT-STATUS-SUMMARY.md",
    ],
    Path("docs/runbooks/cursor.md"): [
        "phase-e-decision-log.md",
        "planning.md",
        "ai-tooling-setup.md",
    ],
    Path("docs/DOCS-INDEX.md"): [
        "phase-e-decision-log.md",
        "ai-tooling-setup.md",
        "security-decision-log.md",
    ],
}

EXTERNAL_PREFIXES = (
    "http://",
    "https://",
    "mailto:",
    "tel:",
    "data:",
    "gh:",
)


def _iter_doc_files() -> list[Path]:
    files: set[Path] = set()
    for root in (REPO_ROOT / "docs", REPO_ROOT / ".cursor"):
        if not root.exists():
            continue
        for path in root.rglob("*"):
            if path.is_file() and path.suffix in MARKDOWN_SUFFIXES:
                files.add(path)
    files.add(REPO_ROOT / "AGENTS.md")
    return sorted(files)


def _normalize_target(raw_target: str) -> str:
    target = raw_target.strip()
    if not target:
        return target
    if " \"" in target:
        target = target.split(" \"", 1)[0]
    if " '" in target:
        target = target.split(" '", 1)[0]
    return target.strip()


def _is_external(target: str) -> bool:
    return target.startswith(EXTERNAL_PREFIXES) or "://" in target


def _resolve_target(source: Path, target: str) -> Path:
    if target.startswith("/"):
        return Path(target)
    return (source.parent / target).resolve()


def validate_links(files: list[Path]) -> list[str]:
    errors: list[str] = []
    for path in files:
        text = path.read_text(encoding="utf-8")
        for match in LINK_RE.finditer(text):
            target = _normalize_target(match.group(1))
            if not target or target.startswith("#") or _is_external(target):
                continue
            local_target = target.split("#", 1)[0].split("?", 1)[0]
            if not local_target:
                continue
            resolved = _resolve_target(path, local_target)
            if not resolved.exists():
                rel_path = path.relative_to(REPO_ROOT)
                errors.append(f"{rel_path}: broken link target '{target}'")
    return errors


def validate_required_files() -> list[str]:
    errors: list[str] = []
    for rel_path in REQUIRED_FILES:
        if not (REPO_ROOT / rel_path).exists():
            errors.append(f"missing required archived stub or compatibility file: {rel_path}")
    return errors


def validate_required_references() -> list[str]:
    errors: list[str] = []
    for rel_path, required_snippets in REQUIRED_REFERENCES.items():
        text = (REPO_ROOT / rel_path).read_text(encoding="utf-8")
        for snippet in required_snippets:
            if snippet not in text:
                errors.append(f"{rel_path}: missing required source-of-truth reference '{snippet}'")
    return errors


def main() -> int:
    files = _iter_doc_files()
    errors = [
        *validate_links(files),
        *validate_required_files(),
        *validate_required_references(),
    ]
    if errors:
        for error in errors:
            print(error, file=sys.stderr)
        return 1
    print(f"docs-consistency OK ({len(files)} files checked)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
