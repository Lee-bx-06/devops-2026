"""Scan source files, repository history, and image metadata for common keys."""

from __future__ import annotations

import argparse
import os
import re
import subprocess
from dataclasses import dataclass
from pathlib import Path

PATTERNS = {
    "openai_style": re.compile(r"sk-[A-Za-z0-9]{20,}"),
    "github_classic": re.compile(r"gh[pousr]_[A-Za-z0-9]{20,}"),
    "github_fine_grained": re.compile(r"github_pat_[A-Za-z0-9_]{20,}"),
    "aws_access_key": re.compile(r"AKIA[0-9A-Z]{16}"),
    "private_key": re.compile(r"-----BEGIN (?:RSA |EC |OPENSSH |DSA )?PRIVATE KEY-----"),
}
EXCLUDED_PARTS = {".git", ".pytest_cache", "__pycache__", "work"}


@dataclass(frozen=True)
class Finding:
    scope: str
    origin: str
    pattern: str
    line: int
    prefix: str


def redact(token: str) -> str:
    return token[:4] + "..."


def scan_text(scope: str, origin: str, text: str) -> list[Finding]:
    findings: list[Finding] = []
    for line_number, line in enumerate(text.splitlines(), 1):
        for name, pattern in PATTERNS.items():
            for match in pattern.finditer(line):
                findings.append(Finding(scope, origin, name, line_number, redact(match.group(0))))
    return findings


def scan_worktree(root: Path) -> list[Finding]:
    findings: list[Finding] = []
    for path in sorted(root.rglob("*")):
        if not path.is_file() or any(part in EXCLUDED_PARTS for part in path.relative_to(root).parts):
            continue
        if path.name == ".env" or (path.name.startswith(".env.") and path.name != ".env.example"):
            continue
        try:
            text = path.read_text(encoding="utf-8")
        except (UnicodeDecodeError, OSError):
            continue
        findings.extend(scan_text("worktree", str(path.relative_to(root)), text))
    env_file = root / ".env"
    if env_file.is_file() and os.name == "posix" and env_file.stat().st_mode & 0o077:
        findings.append(Finding("worktree", ".env", "insecure_permissions", 0, "mode"))
    return findings


def run_text(command: list[str], cwd: Path) -> tuple[int, str]:
    try:
        completed = subprocess.run(
            command,
            cwd=cwd,
            check=False,
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            timeout=120,
        )
    except (FileNotFoundError, subprocess.TimeoutExpired) as exc:
        return 127, str(exc)
    return completed.returncode, completed.stdout + completed.stderr


def repository_context(root: Path) -> Path | None:
    code, output = run_text(["git", "rev-parse", "--show-toplevel"], root)
    if code != 0:
        return None
    try:
        repository_root = Path(output.strip()).resolve()
        root.resolve().relative_to(repository_root)
    except ValueError:
        return None
    return repository_root


def scan_git(root: Path) -> tuple[list[Finding], list[str]]:
    repository_root = repository_context(root)
    if repository_root is None:
        return [], ["Git history unavailable"]

    findings: list[Finding] = []
    warnings: list[str] = []
    code, tracked = run_text(["git", "ls-files"], repository_root)
    if code != 0:
        warnings.append("git ls-files failed")
    else:
        for item in tracked.splitlines():
            if Path(item).name == ".env":
                findings.append(Finding("git", item, "tracked_env_file", 0, ".env"))

    code, history = run_text(["git", "log", "--all", "-p", "--no-color"], repository_root)
    if code != 0:
        warnings.append("git history scan failed")
    else:
        findings.extend(scan_text("git", "all_refs", history))
    return findings, warnings


def scan_image(root: Path, image: str | None) -> tuple[list[Finding], list[str]]:
    if not image:
        return [], ["image history not scanned because no image name was provided"]
    code, history = run_text(["docker", "history", "--no-trunc", image], root)
    if code != 0:
        return [], [f"image history unavailable for {image}"]
    code, environment = run_text(
        ["docker", "image", "inspect", "--format", "{{json .Config.Env}}", image], root
    )
    if code != 0:
        return [], [f"image environment unavailable for {image}"]
    return scan_text("image", image + ":history", history) + scan_text(
        "image", image + ":environment", environment
    ), []


def render(findings: list[Finding], warnings: list[str]) -> str:
    lines = ["E4 B2 secret scan", f"status={'failed' if findings or warnings else 'passed'}"]
    for warning in warnings:
        lines.append(f"warning={warning}")
    for finding in findings:
        lines.append(
            f"finding scope={finding.scope} origin={finding.origin} "
            f"line={finding.line} pattern={finding.pattern} value={finding.prefix}"
        )
    if not findings:
        lines.append("findings=0")
    return "\n".join(lines) + "\n"


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", type=Path, default=Path.cwd())
    parser.add_argument("--image")
    parser.add_argument("--output", type=Path)
    args = parser.parse_args(argv)

    root = args.root.resolve()
    findings = scan_worktree(root)
    git_findings, git_warnings = scan_git(root)
    image_findings, image_warnings = scan_image(root, args.image)
    findings.extend(git_findings)
    findings.extend(image_findings)
    output = render(findings, git_warnings + image_warnings)
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(output, encoding="utf-8")
    print(output, end="")
    return 1 if findings or git_warnings or image_warnings else 0


if __name__ == "__main__":
    raise SystemExit(main())
