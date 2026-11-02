"""Student-specific image tags for the unchanged E5-E7 teaching runner."""
import argparse
import os
from pathlib import Path
import re
import subprocess
import sys

def main():
    root = Path(__file__).resolve().parents[1]
    parser = argparse.ArgumentParser(description="Run E5-E7 with an image tag unique to your student ID")
    parser.add_argument("stage", choices=["doctor", "build", "e5", "e6", "gate"])
    parser.add_argument("--out")
    parser.add_argument("--fixed", action="store_true")
    choice = parser.add_mutually_exclusive_group()
    choice.add_argument("--candidate")
    choice.add_argument("--replay", action="store_true")
    parser.add_argument("--build-timeout", type=int, default=1200)
    args = parser.parse_args()
    sid = subprocess.check_output(["git", "config", "--local", "user.name"], cwd=root, text=True).strip()
    if not re.fullmatch(r"[0-9]{6,16}", sid):
        parser.error("Set git config --local user.name to your numeric student ID")
    service = "buildchecker" if (root / "services/buildchecker").is_dir() else "draft"
    image = f"course1027-{service}:{sid}"
    command = [sys.executable, str(root / "scripts/lab_cloud.py"), args.stage, "--image", image,
               "--build-timeout", str(args.build_timeout)]
    if args.out:
        command += ["--out", args.out]
    if args.fixed:
        command += ["--fixed"]
    if args.candidate:
        command += ["--candidate", args.candidate]
    if args.replay:
        command += ["--replay"]
    print(f"STUDENT_ID={sid}\nSERVICE_IMAGE={image}", flush=True)
    return subprocess.run(command, cwd=root).returncode

if __name__ == "__main__":
    raise SystemExit(main())
