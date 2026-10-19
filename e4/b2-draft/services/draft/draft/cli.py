"""Command-line entry point for the E4 DRAFT skeleton."""

from __future__ import annotations

import argparse
import json
from collections.abc import Sequence
from pathlib import Path

from draft import __version__
from draft import smoke


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="draft")
    subparsers = parser.add_subparsers(dest="command", required=True)
    subparsers.add_parser("version", help="print the service version as JSON")

    smoke_parser = subparsers.add_parser("smoke", help="run the E3 broken-image smoke test")
    smoke_parser.add_argument("--fixture", type=Path, default=Path("/app/fixtures/draft"))
    smoke_parser.add_argument("--timeout", type=int, default=180)
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    if args.command == "version":
        print(json.dumps({"service": "draft", "version": __version__}, sort_keys=True))
        return 0
    if args.command == "smoke":
        return smoke.run_and_print(args.fixture, args.timeout)
    raise AssertionError(f"unhandled command: {args.command}")


if __name__ == "__main__":
    raise SystemExit(main())
