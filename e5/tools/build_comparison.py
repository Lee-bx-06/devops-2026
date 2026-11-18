#!/usr/bin/env python3
"""Build the A-group E5 comparison from per-member verification JSONs.

Usage:
    python build_comparison.py --run 241250014=_execution/e5-leader-verification.json \
                               --run 241250033=_execution/e5-a2-241250033-verification.json \
                               --out _execution/e5-group-comparison-20261029.json
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path

# Fields that must agree across members for the same reference implementation.
SAME_FIELDS = [
    ("unit_tests_passed", "A 轨服务测试项数"),
    ("program_output", "程序输出"),
    ("env_problems", "env.problems"),
    ("declaration_main_o", "make-db 的 main.o 声明"),
    ("declaration_app", "make-db 的 app 声明"),
    ("read_config_h", "config.h 成功读打开位置"),
    ("read_main_c", "main.c 成功读打开位置"),
    ("read_main_o", "main.o 链接期读打开位置"),
    ("read_unused_h", "unused.h 成功读打开"),
    ("trace_files", "trace 文件数"),
    ("trace_lines", "trace 总行数"),
    ("capture_exit", "E5 采集退出码"),
]

# Fields expected to differ per member run.
DIFF_FIELDS = [
    ("source_commit", "运行源码提交"),
    ("evidence_dir", "证据目录"),
]


def flat(v):
    if isinstance(v, list) and v and isinstance(v[0], dict):
        return [f"{item.get('file')}:{item.get('line')}" for item in v]
    return v


def extract(doc):
    opens = doc.get("opens") or {}
    decl = doc.get("declarations") or {}
    return {
        "student_id": doc.get("student_id"),
        "source_commit": doc.get("source_commit"),
        "evidence_dir": doc.get("evidence_dir"),
        "unit_tests_passed": doc.get("unit_tests_passed"),
        "program_output": doc.get("program_output"),
        "env_problems": (doc.get("env") or {}).get("problems"),
        "declaration_main_o": (decl.get("main.o") or {}).get("text"),
        "declaration_app": (decl.get("app") or {}).get("text"),
        "read_config_h": flat(opens.get("config.h")),
        "read_main_c": flat(opens.get("main.c")),
        "read_main_o": flat(opens.get("main.o")),
        "read_unused_h": flat(opens.get("unused.h")),
        "trace_files": (doc.get("trace") or {}).get("files"),
        "trace_lines": (doc.get("trace") or {}).get("lines"),
        "capture_exit": (doc.get("exit_codes") or {}).get("e5"),
        "verification_passed": doc.get("passed"),
    }


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--run", action="append", required=True, help="label=path/to/verification.json")
    ap.add_argument("--out", required=True)
    args = ap.parse_args()

    members = {}
    for spec in args.run:
        label, _, path = spec.partition("=")
        doc = json.loads(Path(path).read_text(encoding="utf-8"))
        members[label] = extract(doc)

    same = []
    for field, title in SAME_FIELDS:
        values = {label: m[field] for label, m in members.items()}
        unique = {json.dumps(v, ensure_ascii=False, sort_keys=True) for v in values.values()}
        same.append({
            "field": field,
            "title": title,
            "values": values,
            "consistent": len(unique) == 1,
        })

    diffs = []
    for field, title in DIFF_FIELDS:
        diffs.append({
            "field": field,
            "title": title,
            "values": {label: m[field] for label, m in members.items()},
        })

    result = {
        "stage": "E5",
        "track": "A",
        "date": "2026-10-29",
        "members": members,
        "consistent_fields": same,
        "expected_differences": diffs,
        "all_consistent": all(item["consistent"] for item in same),
        "all_verified": all(m["verification_passed"] for m in members.values()),
        "note": (
            "同一参考实现、同一 fixture 下，MD/RD 结论与证据位置必须一致；"
            "源码提交、证据目录、镜像 ID 与耗时应按各自运行记录，不作为一致项。"
        ),
    }
    Path(args.out).write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"wrote {args.out}")
    print(f"all_consistent={result['all_consistent']} all_verified={result['all_verified']}")
    for item in same:
        flag = "OK  " if item["consistent"] else "DIFF"
        print(f"  {flag} {item['title']}")
    return 0 if result["all_consistent"] and result["all_verified"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
