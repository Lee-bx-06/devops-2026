"""Build the fixed broken fixture and verify the expected failure."""

from __future__ import annotations

import argparse
import json
import subprocess
import time
from dataclasses import asdict, dataclass
from pathlib import Path

EXPECTED_MARKER = "make: not found"


@dataclass(frozen=True)
class SmokeResult:
    schema_version: str
    fixture: str
    command: list[str]
    docker_server: str | None
    build_exit_code: int | None
    expected_marker: str
    marker_found: bool
    make_error_line: str | None
    make_not_found: bool
    log_tail: list[str]
    timed_out: bool
    duration_seconds: float
    passed: bool
    build_log: str


def assess(
    fixture: Path,
    command: list[str],
    returncode: int | None,
    output: str,
    duration_seconds: float,
    *,
    timed_out: bool = False,
    docker_server: str | None = None,
) -> SmokeResult:
    lines = output.strip().splitlines()
    make_error_line = next((line.strip() for line in lines if EXPECTED_MARKER in line), None)
    marker_found = make_error_line is not None
    passed = not timed_out and returncode not in (None, 0) and marker_found
    return SmokeResult(
        schema_version="1.0",
        fixture=str(fixture),
        command=command,
        docker_server=docker_server,
        build_exit_code=returncode,
        expected_marker=EXPECTED_MARKER,
        marker_found=marker_found,
        make_error_line=make_error_line,
        make_not_found=marker_found,
        log_tail=lines[-8:],
        timed_out=timed_out,
        duration_seconds=round(duration_seconds, 3),
        passed=passed,
        build_log=output,
    )


def execute(fixture: Path, timeout: int) -> SmokeResult:
    fixture = fixture.resolve()
    required = (fixture / "Dockerfile.broken", fixture / "Makefile", fixture / "main.c")
    missing = [str(path) for path in required if not path.is_file()]
    if missing:
        raise FileNotFoundError("missing fixture files: " + ", ".join(missing))

    try:
        server_result = subprocess.run(
            ["docker", "version", "--format", "{{.Server.Version}}"],
            check=False,
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            timeout=30,
        )
        docker_server = server_result.stdout.strip() if server_result.returncode == 0 else None
    except (FileNotFoundError, subprocess.TimeoutExpired):
        docker_server = None

    command = [
        "docker",
        "build",
        "--progress=plain",
        "--no-cache",
        "--file",
        str(fixture / "Dockerfile.broken"),
        str(fixture),
    ]
    started = time.monotonic()
    try:
        completed = subprocess.run(
            command,
            check=False,
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            timeout=timeout,
        )
        output = completed.stdout + completed.stderr
        return assess(
            fixture,
            command,
            completed.returncode,
            output,
            time.monotonic() - started,
            docker_server=docker_server,
        )
    except subprocess.TimeoutExpired as exc:
        stdout = exc.stdout.decode(errors="replace") if isinstance(exc.stdout, bytes) else (exc.stdout or "")
        stderr = exc.stderr.decode(errors="replace") if isinstance(exc.stderr, bytes) else (exc.stderr or "")
        return assess(
            fixture,
            command,
            None,
            stdout + stderr,
            time.monotonic() - started,
            timed_out=True,
            docker_server=docker_server,
        )


def run_and_print(fixture: Path, timeout: int) -> int:
    result = execute(fixture, timeout)
    print(json.dumps(asdict(result), ensure_ascii=False, indent=2, sort_keys=True))
    return 0 if result.passed else 1


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--fixture", type=Path, default=Path("/app/fixtures/draft"))
    parser.add_argument(
        "--timeout",
        type=int,
        default=int(__import__("os").environ.get("DRAFT_BUILD_TIMEOUT_SECONDS", "180")),
    )
    args = parser.parse_args(argv)
    return run_and_print(args.fixture, args.timeout)


if __name__ == "__main__":
    raise SystemExit(main())
