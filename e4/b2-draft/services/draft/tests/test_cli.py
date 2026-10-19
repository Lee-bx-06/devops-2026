from __future__ import annotations

import json

from draft import cli


def test_version_is_machine_readable(capsys):
    assert cli.main(["version"]) == 0
    payload = json.loads(capsys.readouterr().out)
    assert payload == {"service": "draft", "version": "0.1.0"}


def test_parser_requires_a_subcommand():
    parser = cli.build_parser()
    try:
        parser.parse_args([])
    except SystemExit as exc:
        assert exc.code == 2
    else:
        raise AssertionError("missing subcommand must be rejected")
