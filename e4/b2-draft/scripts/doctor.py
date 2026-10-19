"""Collect reproducibility facts without exposing environment values."""

from __future__ import annotations

import json
import os
import platform
import re
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


def command_text(command: list[str], cwd: Path) -> str | None:
    try:
        completed = subprocess.run(
            command,
            cwd=cwd,
            check=False,
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            timeout=20,
        )
    except (FileNotFoundError, subprocess.TimeoutExpired):
        return None
    if completed.returncode != 0:
        return None
    return completed.stdout.strip()


def collect(project_root: Path) -> dict[str, Any]:
    project_root = project_root.resolve()
    repository_root_text = command_text(["git", "rev-parse", "--show-toplevel"], project_root)
    repository_root = Path(repository_root_text) if repository_root_text else project_root
    user_name = command_text(["git", "config", "user.name"], project_root)
    user_email = command_text(["git", "config", "user.email"], project_root)
    commit = command_text(["git", "rev-parse", "HEAD"], project_root)
    status = command_text(["git", "status", "--porcelain"], project_root)
    docker_raw = command_text(["docker", "version", "--format", "{{json .}}"], project_root)
    compose_version = command_text(["docker", "compose", "version", "--short"], project_root)

    docker: dict[str, Any] | None = None
    if docker_raw:
        try:
            docker = json.loads(docker_raw)
        except json.JSONDecodeError:
            docker = {"raw": docker_raw}

    warnings: list[str] = []
    if not user_name or not user_email:
        warnings.append("repository-local Git identity is incomplete")
    elif not re.fullmatch(r"\d{9,12}", user_name):
        warnings.append("git user.name is not a numeric student id")
    if docker is None:
        warnings.append("Docker client/server is unavailable")
    if compose_version is None:
        warnings.append("Docker Compose is unavailable")

    return {
        "schema_version": "1.0",
        "recorded_at": datetime.now(timezone.utc).isoformat(),
        "project_root": str(project_root),
        "repository_root": str(repository_root),
        "repository_commit": commit,
        "repository_dirty": bool(status),
        "git_identity": {
            "name": user_name,
            "email": user_email,
            "looks_like_student_id": bool(user_name and re.fullmatch(r"\d{9,12}", user_name)),
        },
        "host": {
            "system": platform.system(),
            "release": platform.release(),
            "machine": platform.machine(),
            "python": platform.python_version(),
            "uid": os.getuid() if hasattr(os, "getuid") else None,
        },
        "docker": docker,
        "compose_version": compose_version,
        "warnings": warnings,
        "ready": docker is not None
        and compose_version is not None
        and bool(user_email and user_name and re.fullmatch(r"\d{9,12}", user_name)),
    }


def main(argv: list[str] | None = None) -> int:
    import argparse

    parser = argparse.ArgumentParser()
    parser.add_argument("--root", type=Path, default=Path.cwd())
    parser.add_argument("--output", type=Path)
    args = parser.parse_args(argv)
    payload = collect(args.root)
    rendered = json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n"
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(rendered, encoding="utf-8")
    else:
        sys.stdout.write(rendered)
    return 0 if payload["ready"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
