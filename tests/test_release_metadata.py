from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from scripts.check_release_metadata import check_updater_contract, collect_release_metadata_errors


def test_release_metadata_is_consistent() -> None:
    assert collect_release_metadata_errors() == []


def test_updater_contract_disabled_valid() -> None:
    """Updater disabled: pubkey and endpoints empty is valid."""
    assert check_updater_contract({"plugins": {"updater": {"pubkey": "", "endpoints": []}}}) == []


def test_updater_contract_ready_valid() -> None:
    """Updater ready: both pubkey and endpoints set is valid."""
    assert (
        check_updater_contract(
            {
                "plugins": {
                    "updater": {
                        "pubkey": "dummy-pubkey",
                        "endpoints": ["https://example.com/updates/{{target}}/{{arch}}/{{current_version}}"],
                    }
                }
            }
        )
        == []
    )


def test_updater_contract_pubkey_only_invalid() -> None:
    """Pubkey set but endpoints empty is invalid."""
    errs = check_updater_contract({"plugins": {"updater": {"pubkey": "x", "endpoints": []}}})
    assert len(errs) == 1
    assert "pubkey set but endpoints empty" in errs[0]


def test_updater_contract_endpoints_only_invalid() -> None:
    """Endpoints set but pubkey empty is invalid."""
    errs = check_updater_contract({"plugins": {"updater": {"pubkey": "", "endpoints": ["https://x"]}}})
    assert len(errs) == 1
    assert "endpoints set but pubkey empty" in errs[0]
