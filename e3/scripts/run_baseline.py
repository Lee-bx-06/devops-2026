#!/usr/bin/env python3
"""Run the local E3 reference baseline and retain complete, replayable evidence."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import platform
import shutil
import subprocess
import sys
import time
import uuid
from pathlib import Path


SCRIPT = Path(__file__).resolve()
E3_ROOT = SCRIPT.parents[1]
REPO_ROOT = E3_ROOT.parent


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
        if path.is_file() and ".git" not in path.relative_to(root).parts
    }


def json_write(path: Path, value: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(path.suffix + ".tmp")
    temporary.write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    temporary.replace(path)


class Run:
    def __init__(self, root: Path):
        self.root = root
        self.logs = root / "logs"
        self.logs.mkdir(parents=True)
        self.commands: list[dict[str, object]] = []
        self.manifest: dict[str, object] = {
            "schema": "e3-baseline-run-v1",
            "status": "running",
            "started_at_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
            "platform": {"system": platform.system(), "release": platform.release(), "machine": platform.machine(), "python": sys.version},
            "source_snapshot_sha256": {
                "md-rd": tree_hashes(E3_ROOT / "fixtures" / "md-rd"),
                "fixtures": tree_hashes(E3_ROOT / "fixtures"),
            },
            "runner_sha256": sha256_file(SCRIPT),
            "environment_snapshot": {key: os.environ[key] for key in ("CC", "CFLAGS", "MAKEFLAGS") if key in os.environ},
            "observations": {},
            "repositories": {},
            "artifacts": {},
        }
        self.save()

    def save(self) -> None:
        json_write(self.root / "commands.json", self.commands)
        json_write(self.root / "manifest.json", self.manifest)

    def command(self, name: str, argv: list[str], cwd: Path, expected: int = 0) -> subprocess.CompletedProcess[str]:
        index = len(self.commands) + 1
        safe_name = f"{index:03d}-{name}"
        execution_error = None
        try:
            completed = subprocess.run(argv, cwd=cwd, text=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=False)
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
        record = {
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
        if returncode != expected:
            raise RuntimeError(f"{name}: exit {returncode}, expected {expected}; see {stdout_path} and {stderr_path}")
        assert completed is not None
        return completed


def copy_fixture(src: Path, dst: Path) -> None:
    shutil.copytree(src, dst)


def output_of(run: Run, stage: str, cwd: Path, command: list[str]) -> str:
    result = run.command(stage, command, cwd)
    return result.stdout.strip()


def set_mtime(path: Path, epoch: float) -> None:
    os.utime(path, (epoch, epoch))


def record_mtimes(root: Path, paths: list[str]) -> dict[str, float]:
    return {name: (root / name).stat().st_mtime for name in paths}


def run_md_rd(run: Run) -> None:
    repo = run.root / "work" / "md-rd"
    copy_fixture(E3_ROOT / "fixtures" / "md-rd", repo)
    git(run, repo, "mdrd-git-init", "init", "-b", "main")
    for key, value in [("user.name", "E3 Baseline Fixture (automated local fixture)"), ("user.email", "e3-baseline-fixture@localhost"), ("commit.gpgsign", "false")]:
        git(run, repo, f"mdrd-git-config-{key}", "config", key, value)
    commit = git_commit(run, repo, "mdrd-initial")
    git(run, repo, "mdrd-git-tag-initial", "tag", "MD-RD-INITIAL")
    bundle = bundle_and_replay(run, repo, "md-rd", ["MD-RD-INITIAL"])
    run.command("mdrd-clean-1", ["make", "clean"], repo)
    run.command("mdrd-build-1", ["make", "all"], repo)
    first = output_of(run, "mdrd-output-1", repo, ["./app"])
    if first != "1":
        raise AssertionError(f"MD/RD initial output was {first!r}, expected '1'")

    # Normalize stable inputs and products to known ordered mtimes. This avoids
    # relying on filesystem timestamp granularity or future timestamps.
    base = int(time.time()) - 20
    stable = ["Makefile", "main.c", "unused.h", "config.h", "main.o", "app"]
    for name in stable:
        set_mtime(repo / name, base)
    before = record_mtimes(repo, stable)
    (repo / "config.h").write_text("#define VALUE 2\n", encoding="utf-8")
    set_mtime(repo / "config.h", time.time())
    after_config_change = record_mtimes(repo, stable)
    run.command("mdrd-incremental-after-config", ["make", "all"], repo)
    unchanged = output_of(run, "mdrd-output-after-config", repo, ["./app"])
    if unchanged != "1":
        raise AssertionError(f"incremental output after config change was {unchanged!r}, expected stale '1'")

    run.command("mdrd-clean-2", ["make", "clean"], repo)
    run.command("mdrd-build-2", ["make", "all"], repo)
    clean = output_of(run, "mdrd-output-clean-2", repo, ["./app"])
    if clean != "2":
        raise AssertionError(f"clean output after config change was {clean!r}, expected '2'")

    # Put products newer than all unchanged prerequisites, then update only the
    # declared-but-unused header. Make must therefore rebuild main.o for it.
    for name in ["Makefile", "main.c", "config.h"]:
        set_mtime(repo / name, base)
    set_mtime(repo / "main.o", base + 1)
    set_mtime(repo / "app", base + 2)
    before_unused = record_mtimes(repo, ["Makefile", "main.c", "config.h", "unused.h", "main.o", "app"])
    (repo / "unused.h").write_text("/* Changed but still unused. */\n", encoding="utf-8")
    set_mtime(repo / "unused.h", time.time())
    after_unused_change = record_mtimes(repo, ["Makefile", "main.c", "config.h", "unused.h", "main.o", "app"])
    rebuild = run.command("mdrd-incremental-after-unused", ["make", "all"], repo)
    if "-c main.c -o main.o" not in rebuild.stdout:
        raise AssertionError("changing unused.h did not produce the expected main.o compile command")
    after_unused = output_of(run, "mdrd-output-after-unused", repo, ["./app"])
    if after_unused != "2":
        raise AssertionError(f"output after unused.h change was {after_unused!r}, expected '2'")
    run.manifest["observations"]["md-rd"] = {
        "outputs": {"initial": first, "after_config_incremental": unchanged, "after_config_clean": clean, "after_unused_incremental": after_unused},
        "mtimes_before_config_change": before,
        "mtimes_after_config_change_before_make": after_config_change,
        "mtimes_before_unused_change": before_unused,
        "mtimes_after_unused_change_before_make": after_unused_change,
        "mtimes_after_unused_change": record_mtimes(repo, ["Makefile", "main.c", "config.h", "unused.h", "main.o", "app"]),
        "unused_header_change_recompiled_main_o": True,
    }
    run.manifest["repositories"]["md-rd"] = {"identity": "LOCAL automated fixture identity", "commits": {"initial": commit}, "tags": ["MD-RD-INITIAL"], "bundle": bundle}
    run.manifest["oracle_stage_commits"] = {"md-rd": commit}
    run.manifest["artifacts"]["md-rd"] = {"fixture_sha256": tree_hashes(E3_ROOT / "fixtures" / "md-rd"), "run_tree_sha256": tree_hashes(repo)}
    run.save()


def git(run: Run, cwd: Path, name: str, *args: str) -> str:
    return run.command(name, ["git", *args], cwd).stdout.strip()


def git_commit(run: Run, repo: Path, message: str, *pathspecs: str) -> str:
    git(run, repo, f"git-add-{message}", "add", "-A" if not pathspecs else "--", *pathspecs)
    git(run, repo, f"git-commit-{message}", "commit", "-m", message)
    return git(run, repo, f"git-rev-parse-{message}", "rev-parse", "HEAD")


def bundle_and_replay(run: Run, repo: Path, name: str, tags: list[str]) -> dict[str, str]:
    bundle = run.root / "bundles" / f"{name}.bundle"
    bundle.parent.mkdir(parents=True, exist_ok=True)
    git(run, repo, f"bundle-create-{name}", "bundle", "create", str(bundle), "--all")
    verify = run.command(f"bundle-verify-{name}", ["git", "bundle", "verify", str(bundle)], repo)
    restore = run.root / "replay" / name
    restore.parent.mkdir(parents=True, exist_ok=True)
    run.command(f"bundle-clone-{name}", ["git", "clone", str(bundle), str(restore)], run.root)
    restored: dict[str, str] = {}
    for tag in tags:
        original = git(run, repo, f"resolve-original-{name}-{tag}", "rev-parse", f"refs/tags/{tag}^{{commit}}")
        replayed = git(run, restore, f"resolve-replay-{name}-{tag}", "rev-parse", f"refs/tags/{tag}^{{commit}}")
        if original != replayed:
            raise AssertionError(f"bundle replay changed {tag}: {original} != {replayed}")
        restored[tag] = original
    return {"path": str(bundle.relative_to(run.root)), "sha256": sha256_file(bundle), "verification": verify.stdout.strip(), "tag_commits_replayed": restored}


def run_commits(run: Run) -> None:
    repo = run.root / "repos" / "commits"
    copy_fixture(E3_ROOT / "fixtures" / "commits" / "C0", repo)
    git(run, repo, "git-init", "init", "-b", "main")
    for key, value in [("user.name", "E3 Baseline Fixture (automated local fixture)"), ("user.email", "e3-baseline-fixture@localhost"), ("commit.gpgsign", "false")]:
        git(run, repo, f"git-config-{key}", "config", key, value)
    c0 = git_commit(run, repo, "C0")
    git(run, repo, "git-tag-C0", "tag", "C0")

    for name in ["config.h", "main.c", "Makefile"]:
        set_mtime(repo / name, int(time.time()) - 20)
    run.command("c0-clean", ["make", "clean"], repo)
    run.command("c0-build", ["make", "all"], repo)
    out_c0 = output_of(run, "c0-output", repo, ["./app"])
    if out_c0 != "10":
        raise AssertionError(f"C0 output {out_c0!r}, expected '10'")
    run.command("c0-clean-before-c1", ["make", "clean"], repo)

    for path in sorted((E3_ROOT / "fixtures" / "commits" / "C1").iterdir()):
        shutil.copy2(path, repo / path.name)
    c1 = git_commit(run, repo, "C1")
    git(run, repo, "git-tag-C1", "tag", "C1")
    run.command("c1-clean", ["make", "clean"], repo)
    run.command("c1-build", ["make", "all"], repo)
    out_c1 = output_of(run, "c1-output", repo, ["./app"])
    if out_c1 != "12":
        raise AssertionError(f"C1 output {out_c1!r}, expected '12'")
    c1_dry = run.command("c1-make-dryrun", ["make", "-n", "-B", "main.o"], repo).stdout.strip()
    c1_makefile_hash = sha256_file(repo / "Makefile")

    c2_sources = sorted(path for path in (E3_ROOT / "fixtures" / "commits" / "C2").iterdir() if path.suffix in {".c", ".h"})
    c2_source_hashes = {path.name: sha256_file(path) for path in c2_sources}
    live_source_hashes = {path.name: sha256_file(repo / path.name) for path in c2_sources}
    if not c2_source_hashes or c2_source_hashes != live_source_hashes:
        raise AssertionError("C2 source/header fixtures must match C1 before the flags-only change")
    shutil.copy2(E3_ROOT / "fixtures" / "commits" / "C2" / "Makefile", repo / "Makefile")
    c2 = git_commit(run, repo, "C2", "Makefile")
    git(run, repo, "git-tag-C2", "tag", "C2")
    c2_dry = run.command("c2-make-dryrun", ["make", "-n", "-B", "main.o"], repo).stdout.strip()
    if c1_dry == c2_dry:
        raise AssertionError("C1 and C2 make -n -B command snapshots unexpectedly match")
    c2_makefile_hash = sha256_file(repo / "Makefile")
    run.command("c2-incremental-build", ["make", "all"], repo)
    out_c2_incremental = output_of(run, "c2-output-incremental", repo, ["./app"])
    if out_c2_incremental != "12":
        raise AssertionError(f"C2 ordinary incremental output {out_c2_incremental!r}, expected stale '12'")
    run.command("c2-clean", ["make", "clean"], repo)
    run.command("c2-clean-build", ["make", "all"], repo)
    out_c2_clean = output_of(run, "c2-output-clean", repo, ["./app"])
    if out_c2_clean != "19":
        raise AssertionError(f"C2 clean output {out_c2_clean!r}, expected '19'")

    bundle = bundle_and_replay(run, repo, "commits", ["C0", "C1", "C2"])
    run.manifest["repositories"]["commits"] = {"identity": "LOCAL automated fixture identity", "commits": {"C0": c0, "C1": c1, "C2": c2}, "tags": ["C0", "C1", "C2"], "bundle": bundle}
    run.manifest["oracle_stage_commits"] = {"md-rd": run.manifest["repositories"]["md-rd"]["commits"]["initial"], "C0": c0, "C1": c1, "C2": c2}
    run.manifest["observations"]["commits"] = {
        "outputs": {"C0_clean": out_c0, "C1_clean": out_c1, "C2_incremental": out_c2_incremental, "C2_clean": out_c2_clean},
        "C1_C2_makefile_sha256": {"C1": c1_makefile_hash, "C2": c2_makefile_hash},
        "C2_fixture_source_sha256": c2_source_hashes,
        "C1_C2_raw_makefile": {
            "C1": (E3_ROOT / "fixtures" / "commits" / "C1" / "Makefile").read_text(encoding="utf-8"),
            "C2": (E3_ROOT / "fixtures" / "commits" / "C2" / "Makefile").read_text(encoding="utf-8"),
        },
        "C1_C2_make_n_B_main_o": {"C1": c1_dry, "C2": c2_dry},
        "C1_C2_make_n_B_sha256": {"C1": hashlib.sha256(c1_dry.encode()).hexdigest(), "C2": hashlib.sha256(c2_dry.encode()).hexdigest()},
        "C2_flags_only_change": True,
    }
    run.manifest["artifacts"]["commits"] = {"fixture_sha256": tree_hashes(E3_ROOT / "fixtures" / "commits"), "bundle_sha256": bundle["sha256"]}
    run.save()


def write_oracle(root: Path) -> None:
    # Human-maintained, course-derived expected findings. No detector graph is fabricated.
    oracle = {
        "provenance": "COURSE_DERIVED_ORACLE",
        "kind": "human_expected_project_edges_and_findings",
        "project_edges_only": True,
        "excludes_system_headers": True,
        "not_detector_output": True,
        "stages": {
            "md-rd": {"actual_project_includes": [["main.c", "config.h"]], "actual_project_dependencies": [["main.o", "main.c"], ["main.o", "config.h"]], "declared_project_dependencies": [["main.o", "main.c"], ["main.o", "unused.h"]], "expected_findings": [{"type": "MISSING", "target": "main.o", "dependency": "config.h"}, {"type": "REDUNDANT", "target": "main.o", "dependency": "unused.h"}]},
            "C0": {"actual_project_includes": [["main.c", "config.h"]], "actual_project_dependencies": [["main.o", "main.c"], ["main.o", "config.h"]], "declared_project_dependencies": [["main.o", "main.c"], ["main.o", "config.h"]], "expected_findings": []},
            "C1": {"actual_project_includes": [["main.c", "config.h"], ["main.c", "feature.h"]], "actual_project_dependencies": [["main.o", "main.c"], ["main.o", "config.h"], ["main.o", "feature.h"]], "declared_project_dependencies": [["main.o", "main.c"], ["main.o", "config.h"]], "expected_findings": [{"type": "MISSING", "target": "main.o", "dependency": "feature.h"}]},
            "C2": {"actual_project_includes": [["main.c", "config.h"], ["main.c", "feature.h"]], "actual_project_dependencies": [["main.o", "main.c"], ["main.o", "config.h"], ["main.o", "feature.h"]], "declared_project_dependencies": [["main.o", "main.c"], ["main.o", "config.h"]], "expected_findings": [{"type": "MISSING", "target": "main.o", "dependency": "feature.h"}]},
        },
    }
    json_write(root / "oracle.json", oracle)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output-root", type=Path, default=E3_ROOT / "work", help="parent directory for a fresh run directory")
    args = parser.parse_args()
    parent = args.output_root.expanduser().resolve()
    parent.mkdir(parents=True, exist_ok=True)
    root = parent / f"run-{time.strftime('%Y%m%dT%H%M%SZ', time.gmtime())}-{uuid.uuid4().hex[:8]}"
    root.mkdir()
    run = Run(root)
    try:
        versions = {}
        for label, argv in {
            "python": [sys.executable, "--version"],
            "make": ["make", "--version"],
            "compiler": ["cc", "--version"],
            "git": ["git", "--version"],
            "uname": ["uname", "-a"],
        }.items():
            result = run.command(f"version-{label}", argv, REPO_ROOT)
            versions[label] = (result.stdout or result.stderr).splitlines()[0] if (result.stdout or result.stderr) else ""
        run.manifest["tool_versions"] = versions
        write_oracle(root)
        run.manifest["oracle"] = {"path": "oracle.json", "sha256": sha256_file(root / "oracle.json"), "provenance": "COURSE_DERIVED_ORACLE"}
        run_md_rd(run)
        run_commits(run)
        run.manifest["status"] = "succeeded"
        run.manifest["finished_at_utc"] = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
        run.save()
        print(root)
        return 0
    except Exception as error:  # Preserve diagnostics and a failure manifest for any aborted run.
        run.manifest["status"] = "failed"
        run.manifest["failure"] = {"type": type(error).__name__, "message": str(error)}
        run.manifest["finished_at_utc"] = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
        run.save()
        print(f"baseline failed; evidence retained at {root}: {error}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
