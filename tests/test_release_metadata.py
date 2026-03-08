from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from scripts.check_release_metadata import collect_release_metadata_errors


def test_release_metadata_is_consistent() -> None:
    assert collect_release_metadata_errors() == []
