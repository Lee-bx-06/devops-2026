"""Corrected oracle after the B2 E7 merge-gate demonstration."""

from draft.cli import main


def test_b2_version_returns_success_after_recovery():
    assert main(["version"]) == 0
