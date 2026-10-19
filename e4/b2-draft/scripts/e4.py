"""Run E4 steps and retain command-level evidence under work/<run-id>."""

from __future__ import annotations

import argparse
import json
import os
import re
import subprocess
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from doctor import collect as collect_environment
from secret_scan import main as secret_scan_main

BASE_IMAGE = "python:3.13-slim@sha256:70729b46c69b4f1e97c4822c1af3df53a1476cf5ddc6c087c0c10bc3a5678c2f"
DOCKER_CLI_IMAGE = "docker:28.5.1-cli@sha256:9190b0613792e658a7783cf14b2d5ace5941bb68ede7276922ea36ee457d76ad"


class Runner:
    def __init__(self, project_root: Path, work_dir: Path) -> None:
        self.project_root = project_root.resolve()
        self.work_dir = work_dir.resolve()
        self.work_dir.mkdir(parents=True, exist_ok=True)
        self.records: list[dict[str, Any]] = self._load_records()
        self.student_id = self._student_id()
        self.image = f"e4-draft:{self._safe_tag(self.student_id)}"
        self.environment = os.environ.copy()
        self.environment.update(
            {
                "STUDENT_ID": self._safe_tag(self.student_id),
                "DOCKER_GID": self._docker_gid(),
                "COMPOSE_PROJECT_NAME": f"e4-draft-{self._safe_tag(self.student_id)}",
            }
        )

    def _load_records(self) -> list[dict[str, Any]]:
        path = self.work_dir / "commands.json"
        if not path.is_file():
            return []
        try:
            payload = json.loads(path.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, OSError):
            return []
        return payload if isinstance(payload, list) else []

    def _write_records(self) -> None:
        (self.work_dir / "commands.json").write_text(
            json.dumps(self.records, ensure_ascii=False, indent=2) + "\n",
            encoding="utf-8",
        )

    def _git_text(self, *args: str) -> str | None:
        try:
            completed = subprocess.run(
                ["git", *args],
                cwd=self.project_root,
                check=False,
                capture_output=True,
                text=True,
                encoding="utf-8",
                errors="replace",
                timeout=20,
            )
        except (FileNotFoundError, subprocess.TimeoutExpired):
            return None
        return completed.stdout.strip() if completed.returncode == 0 else None

    def _student_id(self) -> str:
        return os.environ.get("STUDENT_ID") or self._git_text("config", "user.name") or "unknown"

    @staticmethod
    def _safe_tag(value: str) -> str:
        safe = re.sub(r"[^A-Za-z0-9_.-]+", "-", value).strip(".-").lower()
        return safe or "unknown"

    @staticmethod
    def _docker_gid() -> str:
        configured = os.environ.get("DOCKER_GID")
        if configured:
            return configured
        socket = Path("/var/run/docker.sock")
        if socket.exists() and hasattr(socket.stat(), "st_gid"):
            return str(socket.stat().st_gid)
        return "0"

    def run(self, name: str, command: list[str], timeout: int = 900) -> subprocess.CompletedProcess[str]:
        started = time.monotonic()
        try:
            completed = subprocess.run(
                command,
                cwd=self.project_root,
                env=self.environment,
                check=False,
                capture_output=True,
                text=True,
                encoding="utf-8",
                errors="replace",
                timeout=timeout,
            )
            timed_out = False
        except subprocess.TimeoutExpired as exc:
            stdout = exc.stdout.decode(errors="replace") if isinstance(exc.stdout, bytes) else (exc.stdout or "")
            stderr = exc.stderr.decode(errors="replace") if isinstance(exc.stderr, bytes) else (exc.stderr or "")
            completed = subprocess.CompletedProcess(command, 124, stdout, stderr)
            timed_out = True

        stdout_path = self.work_dir / f"{name}.stdout.log"
        stderr_path = self.work_dir / f"{name}.stderr.log"
        stdout_path.write_text(completed.stdout, encoding="utf-8")
        stderr_path.write_text(completed.stderr, encoding="utf-8")
        self.records.append(
            {
                "name": name,
                "command": command,
                "exit_code": completed.returncode,
                "timed_out": timed_out,
                "duration_seconds": round(time.monotonic() - started, 3),
                "stdout": stdout_path.name,
                "stderr": stderr_path.name,
            }
        )
        self._write_records()
        return completed

    def manifest(self, status: str) -> None:
        payload = {
            "schema_version": "1.0",
            "recorded_at": datetime.now(timezone.utc).isoformat(),
            "status": status,
            "repository_commit": self._git_text("rev-parse", "HEAD"),
            "repository_dirty": bool(self._git_text("status", "--porcelain")),
            "student_id_source": "STUDENT_ID" if os.environ.get("STUDENT_ID") else "git user.name",
            "image": self.image,
            "base_images": [BASE_IMAGE, DOCKER_CLI_IMAGE],
            "evidence_directory": str(self.work_dir),
            "commands": self.records,
        }
        (self.work_dir / "manifest.json").write_text(
            json.dumps(payload, ensure_ascii=False, indent=2) + "\n",
            encoding="utf-8",
        )

    def doctor(self) -> int:
        payload = collect_environment(self.project_root)
        (self.work_dir / "env.json").write_text(
            json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
            encoding="utf-8",
        )
        self.manifest("doctor-passed" if payload["ready"] else "doctor-failed")
        return 0 if payload["ready"] else 1

    def build(self) -> int:
        completed = self.run(
            "build",
            ["docker", "compose", "--progress", "plain", "build", "draft"],
            timeout=1200,
        )
        (self.work_dir / "build.log").write_text(
            completed.stdout + completed.stderr,
            encoding="utf-8",
        )
        if completed.returncode != 0:
            self.manifest("build-failed")
            return completed.returncode

        inspected = self.run("image-inspect", ["docker", "image", "inspect", self.image], timeout=60)
        if inspected.returncode != 0:
            self.manifest("image-inspect-failed")
            return inspected.returncode
        raw = json.loads(inspected.stdout)
        image_data = {
            "image": self.image,
            "image_id": raw[0].get("Id"),
            "repo_digests": raw[0].get("RepoDigests", []),
            "created": raw[0].get("Created"),
            "repository_commit": self._git_text("rev-parse", "HEAD"),
            "base_images": [BASE_IMAGE, DOCKER_CLI_IMAGE],
        }
        (self.work_dir / "image.json").write_text(
            json.dumps(image_data, ensure_ascii=False, indent=2) + "\n",
            encoding="utf-8",
        )

        toolchain = self.run(
            "toolchain",
            ["docker", "run", "--rm", "--entrypoint", "cat", self.image, "/opt/toolchain.lock"],
            timeout=60,
        )
        (self.work_dir / "toolchain.lock").write_text(toolchain.stdout, encoding="utf-8")
        self.manifest("build-passed" if toolchain.returncode == 0 else "toolchain-failed")
        return toolchain.returncode

    def test(self) -> int:
        completed = self.run(
            "test",
            ["docker", "run", "--rm", "--entrypoint", "python", self.image, "-m", "pytest", "-q", "tests"],
            timeout=300,
        )
        (self.work_dir / "test.log").write_text(completed.stdout + completed.stderr, encoding="utf-8")
        self.manifest("test-passed" if completed.returncode == 0 else "test-failed")
        return completed.returncode

    def smoke(self) -> int:
        completed = self.run(
            "smoke",
            [
                "docker",
                "compose",
                "run",
                "--rm",
                "--no-deps",
                "--entrypoint",
                "python",
                "draft",
                "-m",
                "draft.smoke",
            ],
            timeout=300,
        )
        (self.work_dir / "smoke.json").write_text(completed.stdout, encoding="utf-8")
        (self.work_dir / "smoke.log").write_text(completed.stderr, encoding="utf-8")
        try:
            payload = json.loads(completed.stdout)
        except json.JSONDecodeError:
            payload = None
        passed = completed.returncode == 0 and isinstance(payload, dict) and payload.get("passed") is True
        self.manifest("smoke-passed" if passed else "smoke-failed")
        return 0 if passed else (completed.returncode or 1)

    def scan(self) -> int:
        output = self.work_dir / "secret-scan.txt"
        result = secret_scan_main(
            ["--root", str(self.project_root), "--image", self.image, "--output", str(output)]
        )
        self.manifest("scan-passed" if result == 0 else "scan-failed")
        return result

    def shell(self) -> int:
        work = self.project_root / "work"
        work.mkdir(parents=True, exist_ok=True)
        command = ["docker", "compose", "run", "--rm"]
        if hasattr(os, "getuid"):
            command.extend(["--user", f"{os.getuid()}:{os.getgid()}"])
        command.extend(
            [
                "-e", "HOME=/tmp",
                "-v", f"{work}:/app/work",
                "--entrypoint", "/bin/sh", "draft",
            ]
        )
        return subprocess.call(
            command,
            cwd=self.project_root,
            env=self.environment,
        )

    def clean(self) -> int:
        stopped = self.run("clean-containers", ["docker", "compose", "down", "--remove-orphans"], timeout=120)
        if stopped.returncode != 0:
            self.manifest("clean-failed")
            return stopped.returncode
        removed = self.run("clean-image", ["docker", "image", "rm", self.image], timeout=120)
        self.manifest("cleaned" if removed.returncode == 0 else "clean-failed")
        return removed.returncode


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("action", choices=("all", "doctor", "build", "test", "smoke", "scan", "shell", "clean"))
    parser.add_argument("--work-dir", type=Path, required=True)
    args = parser.parse_args(argv)

    project_root = Path(__file__).resolve().parent.parent
    runner = Runner(project_root, args.work_dir)
    if args.action == "all":
        for action in (runner.doctor, runner.build, runner.test, runner.smoke, runner.scan):
            result = action()
            if result != 0:
                return result
        runner.manifest("succeeded")
        return 0
    return getattr(runner, args.action)()


if __name__ == "__main__":
    raise SystemExit(main())
