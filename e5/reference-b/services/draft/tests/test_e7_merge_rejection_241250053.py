"""Intentional failing oracle used only for the E7 merge-gate demonstration."""

from draft.cli import main


def test_b2_version_oracle_blocks_merge_while_wrong():
    assert main(["version"]) == 1
