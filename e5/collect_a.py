#!/usr/bin/env python3
"""Collect E5 A raw build evidence using the student's existing E4 image."""

import argparse
from datetime import datetime, timezone
import json
import os
from pathlib import Path
import subprocess


ROOT = Path(__file__).resolve().parents[1]


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", required=True, type=Path, help="New evidence directory")
    parser.add_argument("--image", help="Defaults to e4-buildchecker:<local Git student ID>")
    args = parser.parse_args()
    sid = subprocess.check_output(
        ["git", "config", "--local", "user.name"], cwd=ROOT, text=True
    ).strip()
    image_tag = args.image or f"e4-buildchecker:{sid}"
    image = json.loads(subprocess.check_output(
        ["docker", "image", "inspect", image_tag], text=True
    ))[0]
    output = args.out.resolve()
    output.mkdir(parents=True, exist_ok=False)
    evidence = output / "evidence"
    evidence.mkdir()
    runner = output / "runner"
    runner.mkdir()
    source_sha = subprocess.check_output(
        ["git", "rev-parse", "HEAD"], cwd=ROOT, text=True
    ).strip()
    (output / "source-commit.txt").write_text(source_sha + "\n")
    (output / "source-working-tree.patch").write_bytes(subprocess.check_output(
        ["git", "diff", "HEAD", "--", "e4/fixtures/md-rd", "e5/collect_a.py"], cwd=ROOT
    ))
    (output / "image.json").write_text(json.dumps(image, indent=2) + "\n")
    shell = """set -eu
cp -R /input/. /evidence/
cd /evidence
cat /opt/toolchain.lock > toolchain.lock
sha256sum Makefile main.c config.h unused.h > input-sha256.txt
make clean > clean.log 2>&1
mkdir trace
strace -ff -s 4096 -o trace/t -e trace=%file,%process make -p app > make-db.txt 2> build-stderr.log
./app > program-output.txt
cat program-output.txt
"""
    (runner / "capture.sh").write_text(shell)
    command = [
        "docker", "run", "--rm", "--network", "none",
        "--cpus", "1", "--memory", "512m", "--pids-limit", "128",
        "--cap-add", "SYS_PTRACE", "--user", f"{os.getuid()}:{os.getgid()}", "-e", "HOME=/tmp",
        "--cidfile", str(output / "service-container-id.txt"),
        "--mount", f"type=bind,src={ROOT / 'e4/fixtures/md-rd'},dst=/input,readonly",
        "--mount", f"type=bind,src={evidence},dst=/evidence",
        image["Id"], "bash", "-c", shell,
    ]
    (runner / "command.json").write_text(json.dumps(command, indent=2) + "\n")
    meta = {
        "student_id": sid, "source_sha": source_sha,
        "time_utc": datetime.now(timezone.utc).isoformat(),
        "image_tag": image_tag, "image_id": image["Id"],
        "fixture": "e4/fixtures/md-rd", "entrypoint": "e5/collect_a.py",
        "reference": "DevOps_E4_E7_GitHub_20261028: E5 A manual capture",
    }
    (output / "invocation.json").write_text(json.dumps(meta, indent=2) + "\n")
    with (runner / "stdout.log").open("w") as stdout, (runner / "stderr.log").open("w") as stderr:
        result = subprocess.run(command, stdout=stdout, stderr=stderr)
    (runner / "exit-code.json").write_text(json.dumps({"exit_code": result.returncode}) + "\n")
    print(f"EVIDENCE_DIR={output}\nEXIT_CODE={result.returncode}")
    return result.returncode


if __name__ == "__main__":
    raise SystemExit(main())
