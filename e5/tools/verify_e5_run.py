#!/usr/bin/env python3
"""Mechanically verify one E5 (A track) run and emit machine-readable JSON.

Usage:
    python verify_e5_run.py <evidence-dir> [--out result.json] [--expect-commit SHA]

<evidence-dir> is the per-run directory committed under e5/evidence/<学号>-<日期>/,
which contains environment/, build/, e5/, manual-analysis.json.

Exit code 0 = every check passed; 1 = at least one check failed.
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

OPENAT = re.compile(r'openat\((?:[^,]*),\s*"([^"]+)",\s*([^)]*)\)\s*=\s*(-?\d+)')

REQUIRED = [
    "environment/env.json",
    "environment/source-commit.txt",
    "build/build/exit-code.json",
    "build/unit-tests/exit-code.json",
    "build/unit-tests/stdout.log",
    "e5/runner/exit-code.json",
    "e5/evidence/program-output.txt",
    "e5/evidence/make-db.txt",
    "manual-analysis.json",
]


def read_json(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))


def exit_code(ev: Path, rel: str):
    try:
        return read_json(ev / rel).get("exit_code")
    except (FileNotFoundError, ValueError):
        return None


def trace_files(ev: Path):
    d = ev / "e5/evidence/trace"
    return sorted(p for p in d.glob("t.*") if p.is_file()) if d.is_dir() else []


def successful_reads(files):
    """Map basename -> [(trace file, line, fd)] for successful read-only openat."""
    hits = {}
    for path in files:
        with path.open(encoding="utf-8", errors="replace") as fh:
            for lineno, line in enumerate(fh, 1):
                m = OPENAT.search(line)
                if not m:
                    continue
                name, flags, fd = m.group(1), m.group(2), int(m.group(3))
                if fd < 0:
                    continue
                if "O_RDONLY" not in flags or "O_CREAT" in flags:
                    continue
                hits.setdefault(Path(name).name, []).append(
                    {"file": path.name, "line": lineno, "fd": fd}
                )
    return hits


def declaration_lines(make_db: Path):
    out = {}
    for lineno, line in enumerate(make_db.read_text(encoding="utf-8", errors="replace").splitlines(), 1):
        for target in ("main.o", "app"):
            if line.startswith(f"{target}:") and target not in out:
                out[target] = {"line": lineno, "text": line.rstrip()}
    return out


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("evidence")
    ap.add_argument("--out")
    ap.add_argument("--expect-commit")
    args = ap.parse_args()

    ev = Path(args.evidence).resolve()
    checks = []

    def check(name, ok, detail=None):
        checks.append({"check": name, "passed": bool(ok), "detail": detail})
        return bool(ok)

    check("evidence dir exists", ev.is_dir(), str(ev))

    missing = [rel for rel in REQUIRED if not (ev / rel).exists()]
    check("required files present", not missing, {"missing": missing} if missing else None)

    build_rc = exit_code(ev, "build/build/exit-code.json")
    test_rc = exit_code(ev, "build/unit-tests/exit-code.json")
    e5_rc = exit_code(ev, "e5/runner/exit-code.json")
    check("build exit 0", build_rc == 0, build_rc)
    check("unit tests exit 0", test_rc == 0, test_rc)
    check("e5 capture exit 0", e5_rc == 0, e5_rc)

    tests = None
    utest = ev / "build/unit-tests/stdout.log"
    if utest.exists():
        m = re.search(r"(\d+) passed", utest.read_text(encoding="utf-8", errors="replace"))
        tests = int(m.group(1)) if m else None
    check("A track unit tests == 15", tests == 15, tests)

    out_path = ev / "e5/evidence/program-output.txt"
    program_output = out_path.read_text(encoding="utf-8", errors="replace").strip() if out_path.exists() else None
    check("program output is 1", program_output == "1", program_output)

    decl = {}
    mdb = ev / "e5/evidence/make-db.txt"
    if mdb.exists():
        decl = declaration_lines(mdb)
    main_o_decl = decl.get("main.o")
    app_decl = decl.get("app")
    check(
        "make-db declares main.o: main.c unused.h",
        bool(main_o_decl) and main_o_decl["text"].split(":", 1)[1].split() == ["main.c", "unused.h"],
        main_o_decl,
    )
    check("make-db declares app: main.o", bool(app_decl) and app_decl["text"].split(":", 1)[1].split() == ["main.o"], app_decl)

    traces = trace_files(ev)
    total_lines = 0
    for p in traces:
        with p.open(encoding="utf-8", errors="replace") as fh:
            total_lines += sum(1 for _ in fh)
    check("trace files present", len(traces) > 0, len(traces))

    hits = successful_reads(traces) if traces else {}
    cfg = hits.get("config.h", [])
    src = hits.get("main.c", [])
    obj = hits.get("main.o", [])
    unused_ok = hits.get("unused.h", [])
    check("config.h has successful read-only open", len(cfg) > 0, cfg)
    check("main.c has successful read-only open", len(src) > 0, src)
    check("main.o is read by the linker", len(obj) > 0, obj)
    check("unused.h has NO successful read open (RD evidence)", len(unused_ok) == 0, unused_ok)

    env = {}
    env_path = ev / "environment/env.json"
    if env_path.exists():
        try:
            env = read_json(env_path)
        except ValueError:
            env = {}
    check("env problems empty", env.get("problems") == [], env.get("problems"))

    commit = None
    sc = ev / "environment/source-commit.txt"
    if sc.exists():
        commit = sc.read_text(encoding="utf-8").strip()
    check("source commit recorded", bool(commit), commit)
    if args.expect_commit:
        check("source commit matches expected", commit == args.expect_commit, {"actual": commit, "expected": args.expect_commit})

    analysis = {}
    an_path = ev / "manual-analysis.json"
    if an_path.exists():
        try:
            analysis = read_json(an_path)
        except ValueError:
            analysis = {}
    targets = {t.get("target"): t for t in analysis.get("targets", [])}
    main_o = targets.get("main.o", {})
    app = targets.get("app", {})
    check(
        "analysis MD/RD for main.o",
        main_o.get("missing") == ["config.h"] and main_o.get("redundant") == ["unused.h"],
        {"missing": main_o.get("missing"), "redundant": main_o.get("redundant")},
    )
    check(
        "analysis app has empty MD/RD",
        app.get("missing") == [] and app.get("redundant") == [],
        {"missing": app.get("missing"), "redundant": app.get("redundant")},
    )

    # Cross-check every line number claimed in manual-analysis.json against the files.
    bad_refs = []
    for ref in main_o.get("read_evidence", []) + [main_o.get("output_evidence"), main_o.get("declaration_evidence"),
                                                  *app.get("read_evidence", []), app.get("output_evidence"),
                                                  app.get("declaration_evidence")]:
        if not ref or ":" not in ref:
            continue
        rel, _, line_no = ref.rpartition(":")
        path = ev / rel
        try:
            n = int(line_no)
            lines = path.read_text(encoding="utf-8", errors="replace").splitlines()
            if not (1 <= n <= len(lines)):
                bad_refs.append({"ref": ref, "problem": "line out of range"})
        except (FileNotFoundError, ValueError):
            bad_refs.append({"ref": ref, "problem": "file or line unreadable"})
    check("analysis line references resolve", not bad_refs, bad_refs or None)

    result = {
        "evidence_dir": str(ev),
        "source_commit": commit,
        "student_id": (env.get("git") or {}).get("user.name"),
        "exit_codes": {"build": build_rc, "unit_tests": test_rc, "e5": e5_rc},
        "unit_tests_passed": tests,
        "program_output": program_output,
        "trace": {"files": len(traces), "lines": total_lines},
        "declarations": decl,
        "opens": {"config.h": cfg, "main.c": src, "main.o": obj, "unused.h": unused_ok},
        "env": {"problems": env.get("problems"), "warnings": len(env.get("warnings") or []), "spec": env.get("spec")},
        "checks": checks,
        "passed": all(c["passed"] for c in checks),
    }

    text = json.dumps(result, ensure_ascii=False, indent=2)
    if args.out:
        Path(args.out).write_text(text + "\n", encoding="utf-8")
        print(f"wrote {args.out}")
    else:
        print(text)

    failed = [c["check"] for c in checks if not c["passed"]]
    if failed:
        print("FAILED: " + ", ".join(failed), file=sys.stderr)
    return 0 if result["passed"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
