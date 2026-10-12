#!/usr/bin/env python3
"""Run B2's E3 DRAFT baseline and retain replayable evidence."""

from __future__ import annotations

import argparse
import hashlib
import json
import platform
import shutil
import subprocess
import sys
import time
import uuid
from pathlib import Path
from typing import Any


SCRIPT = Path(__file__).resolve()
E3_ROOT = SCRIPT.parents[1]
REPO_ROOT = E3_ROOT.parent
FIXTURE_ROOT = E3_ROOT / "fixtures" / "draft"
BASELINE_PATH = FIXTURE_ROOT / "baseline.json"


def canonical_json(value: object) -> bytes:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def tree_hashes(root: Path) -> dict[str, str]:
    return {
        path.relative_to(root).as_posix(): sha256_file(path)
        for path in sorted(root.rglob("*"))
        if path.is_file()
    }


def normalized_configuration(baseline: dict[str, Any], *, cflags: str | None = None) -> dict[str, Any]:
    environment = baseline["environment"]
    return {
        "base_image": environment["base_image"],
        "build_profile": environment["build_profile"],
        "packages": sorted(environment["packages"]),
        "cflags": cflags if cflags is not None else environment["cflags"],
        "build": baseline["build"],
    }


def configuration_id_for(baseline: dict[str, Any], *, cflags: str | None = None) -> str:
    profile = baseline["environment"]["build_profile"]
    digest = hashlib.sha256(canonical_json(normalized_configuration(baseline, cflags=cflags))).hexdigest()
    return f"cc-{profile}-{digest[:12]}"


def load_and_validate_baseline() -> dict[str, Any]:
    baseline = json.loads(BASELINE_PATH.read_text(encoding="utf-8"))
    build = baseline["build"]
    expected_build = {
        "clean_command": "make clean",
        "command": "make all",
        "verify_command": "make test",
        "project_root": "/workspace/project",
    }
    if build != expected_build:
        raise AssertionError(f"build contract changed: {build!r}")
    if any(token in build["clean_command"] for token in ("&&", "||", ";")):
        raise AssertionError("clean_command must not contain build or verify commands")
    if not build["project_root"].startswith("/"):
        raise AssertionError("project_root must be an absolute POSIX path")
    base_image = baseline["environment"]["base_image"]
    if "@sha256:" not in base_image or base_image.endswith(":latest"):
        raise AssertionError("base image must use an immutable digest and must not use latest")
    expected_id = configuration_id_for(baseline)
    if baseline["environment"]["configuration_id"] != expected_id:
        raise AssertionError(
            f"configuration_id mismatch: {baseline['environment']['configuration_id']} != {expected_id}"
        )
    return baseline


def json_write(path: Path, value: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(path.suffix + ".tmp")
    temporary.write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    temporary.replace(path)


class EvidenceRun:
    def __init__(self, root: Path, baseline: dict[str, Any]):
        self.root = root
        self.logs = root / "logs"
        self.logs.mkdir(parents=True)
        self.commands: list[dict[str, object]] = []
        self.manifest: dict[str, Any] = {
            "schema": "e3-draft-run-v1",
            "owner": "B2",
            "status": "running",
            "started_at_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
            "platform": {
                "system": platform.system(),
                "release": platform.release(),
                "machine": platform.machine(),
                "python": sys.version,
            },
            "repository_commit": self._git_head(),
            "fixture_sha256": tree_hashes(FIXTURE_ROOT),
            "runner_sha256": sha256_file(SCRIPT),
            "contract": {
                "build": baseline["build"],
                "configuration_id": baseline["environment"]["configuration_id"],
                "configuration_input": normalized_configuration(baseline),
                "expected": baseline["expected"],
            },
            "observations": {},
        }
        self.save()

    @staticmethod
    def _git_head() -> str | None:
        result = subprocess.run(
            ["git", "rev-parse", "HEAD"], cwd=REPO_ROOT, text=True,
            stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=False,
        )
        return result.stdout.strip() if result.returncode == 0 else None

    def save(self) -> None:
        json_write(self.root / "commands.json", self.commands)
        json_write(self.root / "manifest.json", self.manifest)

    def command(
        self,
        name: str,
        argv: list[str],
        *,
        cwd: Path = FIXTURE_ROOT,
        expected: int | str = 0,
    ) -> subprocess.CompletedProcess[str]:
        index = len(self.commands) + 1
        safe_name = f"{index:03d}-{name}"
        execution_error: str | None = None
        try:
            completed = subprocess.run(
                argv, cwd=cwd, text=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=False
            )
            returncode = completed.returncode
            stdout = completed.stdout
            stderr = completed.stderr
        except OSError as error:
            completed = None
            returncode = None
            stdout = ""
            stderr = ""
            execution_error = f"{type(error).__name__}: {error}"

        stdout_path = self.logs / f"{safe_name}.stdout.log"
        stderr_path = self.logs / f"{safe_name}.stderr.log"
        stdout_path.write_text(stdout, encoding="utf-8")
        stderr_path.write_text(stderr or (execution_error + "\n" if execution_error else ""), encoding="utf-8")
        record: dict[str, object] = {
            "index": index,
            "name": name,
            "argv": argv,
            "cwd": str(cwd),
            "exit_code": returncode,
            "expected_exit_code": expected,
            "stdout_log": str(stdout_path.relative_to(self.root)),
            "stderr_log": str(stderr_path.relative_to(self.root)),
        }
        if execution_error:
            record["execution_error"] = execution_error
        self.commands.append(record)
        self.save()

        matched = returncode != 0 if expected == "nonzero" else returncode == expected
        if not matched:
            raise RuntimeError(
                f"{name}: exit {returncode}, expected {expected}; see {stdout_path} and {stderr_path}"
            )
        if completed is None:
            raise RuntimeError(f"{name}: command was not started")
        return completed


def assert_broken_diagnostic(result: subprocess.CompletedProcess[str]) -> None:
    diagnostic = (result.stdout + "\n" + result.stderr).lower()
    if "make" not in diagnostic or not any(marker in diagnostic for marker in ("not found", "executable file not found")):
        raise AssertionError("broken build did not expose the expected missing-make diagnostic")


def run_docker(run: EvidenceRun, baseline: dict[str, Any]) -> None:
    docker = shutil.which("docker")
    if not docker:
        raise RuntimeError("Docker CLI is not installed or is not on PATH")

    run_id = run.root.name.lower().replace("_", "-")
    broken_tag = f"nju-e3-draft-broken:{run_id}"
    reference_tag = f"nju-e3-draft-reference:{run_id}"
    container_name = f"e3-b2-{uuid.uuid4().hex[:10]}"

    version = run.command("docker-version", [docker, "version", "--format", "{{json .}}"], cwd=REPO_ROOT)
    broken = run.command(
        "broken-build",
        [docker, "build", "--progress=plain", "-f", "Dockerfile.broken", "-t", broken_tag, "."],
        expected="nonzero",
    )
    assert_broken_diagnostic(broken)

    run.command(
        "reference-build",
        [docker, "build", "--progress=plain", "-f", "Dockerfile.reference", "-t", reference_tag, "."],
    )
    inspect = run.command(
        "reference-inspect",
        [docker, "image", "inspect", reference_tag, "--format", "{{json .}}"],
        cwd=REPO_ROOT,
    )
    image = json.loads(inspect.stdout)
    image_id = image["Id"]
    image_uri = f"nju-e3-draft-reference@{image_id}"

    created = False
    try:
        run.command(
            "container-start",
            [
                docker, "run", "-d", "--name", container_name, "--network", "none",
                "--entrypoint", "sh", reference_tag, "-c", "sleep 600",
            ],
            cwd=REPO_ROOT,
        )
        created = True
        run.command("clean", [docker, "exec", container_name, "make", "clean"], cwd=REPO_ROOT)
        run.command("build", [docker, "exec", container_name, "make", "all"], cwd=REPO_ROOT)
        verify = run.command("verify", [docker, "exec", container_name, "make", "test"], cwd=REPO_ROOT)
        execute = run.command("functional-output", [docker, "exec", container_name, "./hello"], cwd=REPO_ROOT)
        if verify.stdout.strip() != baseline["expected"]["stdout"]:
            raise AssertionError(f"verify output was {verify.stdout.strip()!r}")
        if execute.stdout.strip() != baseline["expected"]["stdout"]:
            raise AssertionError(f"functional output was {execute.stdout.strip()!r}")
    finally:
        if created:
            run.command("container-remove", [docker, "rm", "-f", container_name], cwd=REPO_ROOT)

    run.manifest["observations"] = {
        "docker_version": json.loads(version.stdout),
        "broken_build": {
            "exit_code_nonzero": True,
            "diagnostic": "missing make/toolchain",
            "dockerfile": "Dockerfile.broken",
        },
        "reference_build": {
            "dockerfile": "Dockerfile.reference",
            "tag": reference_tag,
            "image_id": image_id,
            "image_uri": image_uri,
            "configuration_id": baseline["environment"]["configuration_id"],
            "clean_exit_code": 0,
            "build_exit_code": 0,
            "verify_exit_code": 0,
            "functional_exit_code": 0,
            "stdout": baseline["expected"]["stdout"],
        },
    }
    run.save()


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--output-root",
        type=Path,
        default=E3_ROOT / "work" / "draft",
        help="parent directory for a new immutable evidence directory",
    )
    parser.add_argument(
        "--verify-only",
        action="store_true",
        help="validate fixture metadata and configuration mapping without Docker",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    baseline = load_and_validate_baseline()
    if args.verify_only:
        print(json.dumps({
            "status": "verified",
            "configuration_id": configuration_id_for(baseline),
            "fixture_sha256": tree_hashes(FIXTURE_ROOT),
        }, ensure_ascii=False, indent=2))
        return 0

    output_root = args.output_root.resolve()
    output_root.mkdir(parents=True, exist_ok=True)
    run_root = output_root / f"draft-run-{time.strftime('%Y%m%dT%H%M%SZ', time.gmtime())}-{uuid.uuid4().hex[:8]}"
    run = EvidenceRun(run_root, baseline)
    try:
        run_docker(run, baseline)
        run.manifest["status"] = "succeeded"
        run.manifest["finished_at_utc"] = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
        run.save()
        print(run_root)
        return 0
    except Exception as error:
        run.manifest["status"] = "failed"
        run.manifest["failure"] = {"type": type(error).__name__, "message": str(error)}
        run.manifest["finished_at_utc"] = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
        run.save()
        print(f"DRAFT baseline failed; evidence retained at {run_root}: {error}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
