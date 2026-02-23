#!/usr/bin/env bash
set -euo pipefail

# Alpha: минимальный порог для ускорения разработки; на поздних этапах поднимать (e.g. 85%)
coverage_file="coverage.json"
fail_under="20"
base_ref=""
exclude_patterns=""

usage() {
  cat <<'EOF'
Usage: ./scripts/check_new_code_coverage.sh [options]

Options:
  --coverage-file <path>  Coverage JSON file (default: coverage.json)
  --fail-under <percent>  Minimum required coverage for changed executable lines (default: 20)
  --base <git-ref>        Git base ref for diff (default: auto-detect)
  --exclude <pattern>     Exclude file paths containing pattern from aggregate (repeatable)
  -h, --help              Show this help
EOF
}

while [[ $# -gt 0 ]]; do
  case "$1" in
    --coverage-file)
      coverage_file="${2:-}"
      shift 2
      ;;
    --fail-under)
      fail_under="${2:-}"
      shift 2
      ;;
    --base)
      base_ref="${2:-}"
      shift 2
      ;;
    --exclude)
      exclude_patterns="${exclude_patterns}${exclude_patterns:+ }${2:-}"
      shift 2
      ;;
    -h|--help)
      usage
      exit 0
      ;;
    *)
      echo "Unknown option: $1" >&2
      usage >&2
      exit 2
      ;;
  esac
done

if [[ ! -f "${coverage_file}" ]]; then
  echo "Coverage file not found: ${coverage_file}" >&2
  exit 1
fi

if [[ -z "${base_ref}" ]]; then
  if [[ "${GITHUB_EVENT_NAME:-}" == "pull_request" && -n "${GITHUB_BASE_REF:-}" ]]; then
    base_ref="origin/${GITHUB_BASE_REF}"
  elif git rev-parse --verify --quiet origin/main >/dev/null; then
    base_ref="origin/main"
  elif git rev-parse --verify --quiet HEAD~1 >/dev/null; then
    base_ref="HEAD~1"
  else
    echo "Unable to auto-detect base ref (origin/main or HEAD~1 missing)." >&2
    exit 1
  fi
fi

if ! git rev-parse --verify --quiet "${base_ref}" >/dev/null; then
  case "${base_ref}" in
    origin/*)
      branch="${base_ref#origin/}"
      git fetch --no-tags --prune --depth=300 origin \
        "refs/heads/${branch}:refs/remotes/origin/${branch}" >/dev/null 2>&1 || true
      ;;
  esac
fi

if ! git rev-parse --verify --quiet "${base_ref}" >/dev/null; then
  echo "Base ref is not available: ${base_ref}" >&2
  exit 1
fi

python - "${coverage_file}" "${base_ref}" "${fail_under}" "${exclude_patterns}" <<'PY'
from __future__ import annotations

import json
import os
import re
import subprocess
import sys
from pathlib import Path

coverage_path = Path(sys.argv[1])
base_ref = sys.argv[2]
fail_under = float(sys.argv[3])
exclude_patterns = (sys.argv[4] or "").strip().split()

if not coverage_path.is_file():
    raise SystemExit(f"Coverage file not found: {coverage_path}")

diff_cmd = ["git", "diff", "--unified=0", "--no-color", f"{base_ref}...HEAD", "--", "src/voiceforge"]
diff = subprocess.run(diff_cmd, check=True, text=True, capture_output=True).stdout

changed_lines_by_file: dict[str, set[int]] = {}
current_file: str | None = None
hunk_re = re.compile(r"@@ -\d+(?:,\d+)? \+(\d+)(?:,(\d+))? @@")

for raw_line in diff.splitlines():
    if raw_line.startswith("+++ b/"):
        path = raw_line[6:]
        if path.startswith("src/voiceforge/") and path.endswith(".py"):
            current_file = os.path.normpath(path)
            changed_lines_by_file.setdefault(current_file, set())
        else:
            current_file = None
        continue
    if current_file is None:
        continue
    if not raw_line.startswith("@@"):
        continue
    match = hunk_re.match(raw_line)
    if not match:
        continue
    start = int(match.group(1))
    count = int(match.group(2) or "1")
    if count <= 0:
        continue
    changed_lines_by_file[current_file].update(range(start, start + count))

if not changed_lines_by_file:
    print(f"new-code-coverage: no changed python lines under src/voiceforge vs {base_ref}")
    raise SystemExit(0)

coverage = json.loads(coverage_path.read_text())
files_cov: dict[str, dict[str, list[int]]] = coverage.get("files", {})


def find_cov_entry(path: str) -> dict[str, list[int]] | None:
    norm = os.path.normpath(path)
    if norm in files_cov:
        return files_cov[norm]
    for key, value in files_cov.items():
        if os.path.normpath(key).endswith(norm):
            return value
    return None


total_covered = 0
total_relevant = 0
rows: list[tuple[str, int, int, float, bool]] = []

for path in sorted(changed_lines_by_file):
    entry = find_cov_entry(path)
    if entry is None:
        rows.append((path, 0, 0, 100.0, True))
        continue
    changed = changed_lines_by_file[path]
    executed = set(entry.get("executed_lines", []))
    missing = set(entry.get("missing_lines", []))
    measurable = executed | missing
    relevant = changed & measurable
    covered = relevant & executed
    relevant_n = len(relevant)
    covered_n = len(covered)
    pct = 100.0 if relevant_n == 0 else (covered_n * 100.0 / relevant_n)
    excluded = any(p in path for p in exclude_patterns)
    rows.append((path, covered_n, relevant_n, pct, excluded))
    if not excluded:
        total_covered += covered_n
        total_relevant += relevant_n

print(f"new-code-coverage: base={base_ref}, threshold={fail_under:.1f}%")
for path, covered_n, relevant_n, pct, excluded in rows:
    suffix = " (excluded)" if excluded else ""
    print(f"  {path}: {covered_n}/{relevant_n} ({pct:.1f}%){suffix}")

if total_relevant == 0:
    print("new-code-coverage: no executable changed lines detected")
    raise SystemExit(0)

overall = total_covered * 100.0 / total_relevant
print(f"new-code-coverage-summary: {total_covered}/{total_relevant} ({overall:.1f}%)")
if overall < fail_under:
    raise SystemExit(
        f"new-code-coverage FAILED: {overall:.1f}% < {fail_under:.1f}% on changed executable lines"
    )
print("new-code-coverage: OK")
PY
