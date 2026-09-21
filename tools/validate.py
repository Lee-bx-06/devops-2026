#!/usr/bin/env python3
"""A09/B09 公共契约校验器（E2，只定义不部署）。

设计取舍：本校验器只用 Python 标准库，不依赖 jsonschema。原因是课堂环境无法
保证能装第三方包，而第 25 页要求「运行 validate.py」必须当场可跑。

它不是通用 JSON Schema 引擎，而是从 docs/interfaces/task.schema.json 中**读取**
枚举、正则与必填清单，再镜像执行跨字段约束。这样 schema 与校验器不会各说各话：
改了 schema 里的枚举，校验器立即跟着变；两者不一致会直接报错。

用法：
    python3 tools/validate.py                # 校验仓库内全部样例（正例 + 负例）
    python3 tools/validate.py path/to/x.json # 校验指定文件，按正例处理
"""
from __future__ import annotations

import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCHEMA_PATH = ROOT / "docs" / "interfaces" / "task.schema.json"
SAMPLES = ROOT / "docs" / "interfaces" / "samples"

ENVELOPE_KINDS = ("create_request", "job", "artifact_record")
ARTIFACT_BODY_KINDS = ("actual_graph", "declared_graph", "error_report")
KINDS = ENVELOPE_KINDS + ARTIFACT_BODY_KINDS


class Schema:
    """从 task.schema.json 抽取校验所需的常量，避免校验器与 schema 漂移。"""

    def __init__(self, doc: dict):
        d = doc["$defs"]
        self.job_types = set(d["job_type"]["enum"])
        self.statuses = set(d["job_status"]["enum"])
        self.finding_types = set(d["finding_type"]["enum"])
        self.schema_version = d["create_request"]["properties"]["schema_version"]["const"]
        self.error_code_re = re.compile(d["error_code"]["pattern"])
        self.artifact_type_re = re.compile(d["artifact_type"]["pattern"])
        self.job_id_re = re.compile(d["job_id"]["pattern"])
        self.trace_id_re = re.compile(d["trace_id"]["pattern"])
        self.artifact_uri_re = re.compile(d["artifact_uri"]["pattern"])
        self.commit_re = re.compile(d["commit_sha"]["pattern"])
        self.container_root_re = re.compile(
            d["actual_graph"]["properties"]["project_root"]["pattern"])
        self.sha256_re = re.compile(d["sha256"]["pattern"])
        self.iso_re = re.compile(d["iso8601"]["pattern"])

        self.envelope_fields = {k: set(d[k]["properties"]) for k in KINDS}
        self.envelope_required = {k: set(d[k]["required"]) for k in KINDS}
        self.artifact_required = set(d["artifact"]["required"])
        self.artifact_fields = set(d["artifact"]["properties"])
        self.finding_required = set(d["finding"]["required"])
        self.error_required = set(d["error"]["required"])
        self.error_fields = set(d["error"]["properties"])
        self.execution_required = set(d["execution"]["required"])
        self.execution_fields = set(d["execution"]["properties"])
        self.evidence_kinds = set(d["finding_evidence"]["properties"]["kind"]["enum"])
        self.actual_observations = set(
            d["actual_graph_dependency"]["properties"]["observation"]["enum"])

        # 每类 job 的 input 必填项与 input/output 的 $def 名
        self.input_required: dict[str, set] = {}
        for jt in self.job_types:
            def_name = "input_" + jt.lower()
            self.input_required[jt] = set(d[def_name]["required"])

        self.output_required: dict[str, set] = {}
        for jt in self.job_types:
            def_name = "output_" + jt.lower()
            node = d.get(def_name)
            self.output_required[jt] = set(node["required"]) if node else set()


def _s(value) -> bool:
    return isinstance(value, str) and bool(value)


def _is_int(value) -> bool:
    return isinstance(value, int) and not isinstance(value, bool)


class Validator:
    def __init__(self, schema: Schema):
        self.s = schema

    # ---------- 基础类型 ----------

    def check_str(self, value, label, errors, pattern: re.Pattern | None = None):
        if not _s(value):
            errors.append(f"{label} 必须是非空字符串")
            return
        if pattern is not None and not pattern.match(value):
            errors.append(f"{label} 格式不符：{value!r} 不匹配 {pattern.pattern}")

    def check_commit(self, value, label, errors):
        self.check_str(value, label, errors, self.s.commit_re)

    def check_pattern(self, value, label, errors, pattern, name):
        if not _s(value):
            errors.append(f"{label} 必须是非空字符串")
        elif not pattern.match(value):
            errors.append(f"{label} 格式不符：{value!r} 不满足 {name}")

    # ---------- finding / error / artifact ----------

    def check_finding(self, value, label, errors):
        if not isinstance(value, dict):
            errors.append(f"{label} 必须是对象")
            return
        missing = self.s.finding_required - set(value)
        if missing:
            errors.append(f"{label} 缺少 finding 必填字段: {', '.join(sorted(missing))}")
        self.check_str(value.get("id"), f"{label}.id", errors)
        if value.get("type") not in self.s.finding_types:
            errors.append(
                f"{label}.type 非法: {value.get('type')!r}，finding 只能是 "
                f"{'/'.join(sorted(self.s.finding_types))}（第 9 页）")
        for f in ("target", "dependency", "detector", "message"):
            self.check_str(value.get(f), f"{label}.{f}", errors)
        self.check_commit(value.get("commit"), f"{label}.commit", errors)

        loc = value.get("location")
        if not isinstance(loc, dict) or not _s(loc.get("path")):
            errors.append(f"{label}.location.path 缺失（第 10 页要求「完整报告还要有位置」）")

        ev = value.get("evidence")
        if not isinstance(ev, list) or not ev:
            errors.append(f"{label}.evidence 必须是非空数组（第 10 页要求「完整报告还要有证据」）")
        else:
            for i, item in enumerate(ev):
                if not isinstance(item, dict):
                    errors.append(f"{label}.evidence[{i}] 必须是对象")
                    continue
                if item.get("kind") not in self.s.evidence_kinds:
                    errors.append(f"{label}.evidence[{i}].kind 非法: {item.get('kind')!r}")
                self.check_str(item.get("detail"), f"{label}.evidence[{i}].detail", errors)
                if item.get("artifact_uri") is not None:
                    self.check_pattern(item["artifact_uri"], f"{label}.evidence[{i}].artifact_uri",
                                       errors, self.s.artifact_uri_re, "artifact_uri")

    def check_error(self, value, label, errors):
        if not isinstance(value, dict):
            errors.append(f"{label} 必须是对象（FAILED/TIMED_OUT 必须有 error，第 8 页）")
            return
        missing = self.s.error_required - set(value)
        if missing:
            errors.append(f"{label} 缺少必填字段: {', '.join(sorted(missing))}")
        unknown = set(value) - self.s.error_fields
        if unknown:
            errors.append(f"{label} 含未定义字段: {', '.join(sorted(unknown))}")
        code = value.get("code")
        if not _s(code):
            errors.append(f"{label}.code 必须是非空字符串")
        elif not self.s.error_code_re.match(code):
            errors.append(
                f"error.code 非法: {code!r} 不在命名空间内（第 9 页：系统错误用 "
                f"ENV_3xxx/EXEC_4xxx/ANALYSIS_5xxx；MISSING/REDUNDANT 属 findings，不是 error）")
        self.check_str(value.get("message"), f"{label}.message", errors)
        if "retryable" in value and not isinstance(value["retryable"], bool):
            errors.append(f"{label}.retryable 必须是布尔值")

    def check_artifact(self, value, label, errors, allow_kind=False):
        if not isinstance(value, dict):
            errors.append(f"{label} 必须是对象")
            return
        required = self.s.artifact_required
        fields = self.s.artifact_fields
        if allow_kind:
            required = required | {"kind", "schema_version"}
            fields = fields | {"kind", "schema_version"}
        missing = required - set(value)
        if missing:
            errors.append(f"{label} 缺少 artifact 必填字段: {', '.join(sorted(missing))}")
        unknown = set(value) - fields
        if unknown:
            errors.append(f"{label} 含未定义字段: {', '.join(sorted(unknown))}")
        if allow_kind:
            if value.get("kind") != "artifact_record":
                errors.append(f"{label}.kind 必须是 artifact_record")
            if value.get("schema_version") != self.s.schema_version:
                errors.append(f"{label}.schema_version 必须是 {self.s.schema_version}")
        self.check_str(value.get("artifact_id"), f"{label}.artifact_id", errors)
        self.check_pattern(value.get("type"), f"{label}.type", errors,
                           self.s.artifact_type_re, "artifact_type")
        self.check_pattern(value.get("uri"), f"{label}.uri", errors,
                           self.s.artifact_uri_re, "artifact_uri（第 24 页：artifact://pair09/...）")
        self.check_str(value.get("media_type"), f"{label}.media_type", errors)
        self.check_pattern(value.get("producer_job_id"), f"{label}.producer_job_id", errors,
                           self.s.job_id_re, "job_id")
        self.check_commit(value.get("commit"), f"{label}.commit", errors)
        self.check_str(value.get("configuration_id"), f"{label}.configuration_id", errors)
        self.check_pattern(value.get("sha256"), f"{label}.sha256", errors,
                           self.s.sha256_re, "sha256")
        if value.get("size_bytes") is not None and not _is_int(value.get("size_bytes")):
            errors.append(f"{label}.size_bytes 必须是整数或 null")

    def check_counts(self, value, label, errors):
        if not isinstance(value, dict):
            errors.append(f"{label} 必须是对象")
            return
        unknown = set(value) - {"missing", "redundant"}
        if unknown:
            errors.append(f"{label} 含未定义字段: {', '.join(sorted(unknown))}")
        for field in ("missing", "redundant"):
            if not _is_int(value.get(field)) or value[field] < 0:
                errors.append(f"{label}.{field} 必须是 >=0 的整数")

    def check_counts_match_findings(self, counts, findings, label, errors):
        if not isinstance(counts, dict) or not isinstance(findings, list):
            return
        expected = {
            "missing": sum(1 for f in findings
                           if isinstance(f, dict) and f.get("type") == "MISSING"),
            "redundant": sum(1 for f in findings
                             if isinstance(f, dict) and f.get("type") == "REDUNDANT"),
        }
        for field, actual in expected.items():
            if counts.get(field) != actual:
                errors.append(
                    f"{label}.counts.{field} 必须等于 findings 中 {field.upper()} "
                    f"记录数，期望 {actual}，实际 {counts.get(field)!r}")

    def check_actual_graph_dependency(self, value, label, errors):
        if not isinstance(value, dict):
            errors.append(f"{label} 必须是对象")
            return
        unknown = set(value) - {"path", "observation", "evidence_uri"}
        if unknown:
            errors.append(f"{label} 含未定义字段: {', '.join(sorted(unknown))}")
        self.check_str(value.get("path"), f"{label}.path", errors)
        if value.get("observation") not in self.s.actual_observations:
            errors.append(
                f"{label}.observation 非法: {value.get('observation')!r}，"
                f"必须是 {'/'.join(sorted(self.s.actual_observations))}")
        if value.get("evidence_uri") is not None:
            self.check_pattern(value["evidence_uri"], f"{label}.evidence_uri", errors,
                               self.s.artifact_uri_re, "artifact_uri")

    def check_declared_graph_dependency(self, value, label, errors):
        if not isinstance(value, dict):
            errors.append(f"{label} 必须是对象")
            return
        unknown = set(value) - {"path", "makefile_path", "line", "rule"}
        if unknown:
            errors.append(f"{label} 含未定义字段: {', '.join(sorted(unknown))}")
        self.check_str(value.get("path"), f"{label}.path", errors)
        self.check_str(value.get("makefile_path"), f"{label}.makefile_path", errors)
        if not _is_int(value.get("line")) or value["line"] < 1:
            errors.append(f"{label}.line 必须是 >=1 的整数")
        if value.get("rule") is not None and not _s(value.get("rule")):
            errors.append(f"{label}.rule 必须是非空字符串或 null")

    def check_artifact_body(self, kind, value, label, errors):
        """校验 ACTUAL_GRAPH / DECLARED_GRAPH / ERROR_REPORT 的文件本体。"""
        missing = self.s.envelope_required[kind] - set(value)
        if missing:
            errors.append(f"{label} 缺少 {kind} 必填字段: {', '.join(sorted(missing))}")
        unknown = set(value) - self.s.envelope_fields[kind]
        if unknown:
            errors.append(f"{label} 含未定义字段: {', '.join(sorted(unknown))}")
        if value.get("kind") != kind:
            errors.append(f"{label}.kind 必须是 {kind}")
        if value.get("schema_version") != self.s.schema_version:
            errors.append(f"{label}.schema_version 必须是 {self.s.schema_version}")
        self.check_commit(value.get("commit"), f"{label}.commit", errors)
        self.check_str(value.get("configuration_id"), f"{label}.configuration_id", errors)

        if kind == "actual_graph":
            self.check_str(
                value.get("project_root"), f"{label}.project_root", errors,
                self.s.container_root_re)
            targets = value.get("targets")
            if not isinstance(targets, list) or not targets:
                errors.append(f"{label}.targets 必须是非空数组")
                return
            for i, target in enumerate(targets):
                item_label = f"{label}.targets[{i}]"
                if not isinstance(target, dict):
                    errors.append(f"{item_label} 必须是对象")
                    continue
                self.check_str(target.get("target"), f"{item_label}.target", errors)
                deps = target.get("dependencies")
                if not isinstance(deps, list):
                    errors.append(f"{item_label}.dependencies 必须是数组")
                    continue
                for j, dep in enumerate(deps):
                    self.check_actual_graph_dependency(
                        dep, f"{item_label}.dependencies[{j}]", errors)

        elif kind == "declared_graph":
            targets = value.get("targets")
            if not isinstance(targets, list) or not targets:
                errors.append(f"{label}.targets 必须是非空数组")
                return
            for i, target in enumerate(targets):
                item_label = f"{label}.targets[{i}]"
                if not isinstance(target, dict):
                    errors.append(f"{item_label} 必须是对象")
                    continue
                self.check_str(target.get("target"), f"{item_label}.target", errors)
                deps = target.get("prerequisites")
                if not isinstance(deps, list):
                    errors.append(f"{item_label}.prerequisites 必须是数组")
                    continue
                for j, dep in enumerate(deps):
                    self.check_declared_graph_dependency(
                        dep, f"{item_label}.prerequisites[{j}]", errors)

        elif kind == "error_report":
            self.check_counts(value.get("counts"), f"{label}.counts", errors)
            findings = value.get("findings")
            if not isinstance(findings, list):
                errors.append(f"{label}.findings 必须是数组")
            else:
                for i, finding in enumerate(findings):
                    self.check_finding(finding, f"{label}.findings[{i}]", errors)
                self.check_counts_match_findings(
                    value.get("counts"), findings, label, errors)

    # ---------- execution ----------

    def check_execution(self, value, label, errors):
        if not isinstance(value, dict):
            errors.append(f"{label} 必须是对象")
            return
        missing = self.s.execution_required - set(value)
        if missing:
            errors.append(f"{label} 缺少必填字段: {', '.join(sorted(missing))}")
        unknown = set(value) - self.s.execution_fields
        if unknown:
            errors.append(f"{label} 含未定义字段: {', '.join(sorted(unknown))}")
        if not _is_int(value.get("attempt")) or value.get("attempt", 0) < 1:
            errors.append(f"{label}.attempt 必须是 >=1 的整数")
        for f in ("queued_at", "started_at", "finished_at"):
            v = value.get(f)
            if v is None:
                if f == "queued_at":
                    errors.append(f"{label}.queued_at 不允许为 null")
                continue
            if not _s(v) or not self.s.iso_re.match(v):
                errors.append(f"{label}.{f} 必须是 ISO8601 或 null")
        if value.get("duration_ms") is not None and not _is_int(value.get("duration_ms")):
            errors.append(f"{label}.duration_ms 必须是整数或 null")

    # ---------- input ----------

    def check_repository(self, value, label, errors):
        if not isinstance(value, dict):
            errors.append(f"{label} 必须是对象")
            return
        self.check_str(value.get("url"), f"{label}.url", errors)
        self.check_commit(value.get("commit"), f"{label}.commit", errors)

    def check_environment(self, value, label, errors):
        if not isinstance(value, dict):
            errors.append(f"{label} 必须是对象")
            return
        self.check_str(value.get("image_uri"), f"{label}.image_uri", errors)
        self.check_str(value.get("configuration_id"), f"{label}.configuration_id", errors)

    def check_build(self, value, label, errors, extra_required=()):
        if not isinstance(value, dict):
            errors.append(f"{label} 必须是对象")
            return
        need = {"command", *extra_required}
        missing = need - set(value)
        if missing:
            errors.append(f"{label} 缺少必填字段: {', '.join(sorted(missing))}")
        self.check_str(value.get("command"), f"{label}.command", errors)

    def check_input(self, job_type, value, label, errors):
        """第 20-23 页：服务专有输入。缺失必填项即违反契约，应在创建时被拒。"""
        if not isinstance(value, dict):
            errors.append(f"{label} 必须是对象")
            return
        required = self.s.input_required.get(job_type, set())
        missing = required - set(value)
        if missing:
            errors.append(
                f"input 缺少 {job_type} 的必填字段: {', '.join(sorted(missing))}")

        if "repository" in value:
            self.check_repository(value["repository"], f"{label}.repository", errors)
        if "environment" in value:
            self.check_environment(value["environment"], f"{label}.environment", errors)
        if "build" in value:
            extra = ("clean_command", "project_root") if job_type == "FULL_CHECK" else ()
            self.check_build(value["build"], f"{label}.build", errors, extra)

        if job_type == "DRAFT" and "limits" in value:
            limits = value["limits"]
            if not isinstance(limits, dict):
                errors.append(f"{label}.limits 必须是对象")
            else:
                for f in ("max_iterations", "timeout_seconds"):
                    if not _is_int(limits.get(f)) or limits[f] < 1:
                        errors.append(f"{label}.limits.{f} 必须是 >=1 的整数（第 20 页要求显式上限）")

        if job_type == "INCREMENTAL_CHECK":
            self.check_commit(value.get("base_commit"), f"{label}.base_commit", errors)
            baseline = value.get("baseline")
            # 第 12、22、25 页：baseline 必填，缺 baseline 必须被拒
            if not isinstance(baseline, dict):
                errors.append(
                    "input.baseline 缺失或不是对象：INCREMENTAL_CHECK 必须携带基线，"
                    "缺 baseline 应被拒绝（第 12、22、25 页）")
            else:
                for f in ("actual_graph_uri", "commit", "configuration_id"):
                    if f not in baseline:
                        errors.append(f"input.baseline 缺少必填字段: {f}")
                self.check_pattern(baseline.get("actual_graph_uri"), "input.baseline.actual_graph_uri",
                                   errors, self.s.artifact_uri_re, "artifact_uri")
                self.check_commit(baseline.get("commit"), "input.baseline.commit", errors)
                self.check_str(baseline.get("configuration_id"),
                               "input.baseline.configuration_id", errors)

        if job_type == "REPAIR":
            self.check_str(value.get("makefile_path"), f"{label}.makefile_path", errors)
            if "md_report" in value:
                self.check_artifact(value["md_report"], f"{label}.md_report", errors)
                # 第 12、23 页：MDFixer 只消费 MD，报告必须是 ERROR_REPORT
                if isinstance(value["md_report"], dict) and value["md_report"].get("type") != "ERROR_REPORT":
                    errors.append(
                        f"input.md_report.type 必须是 ERROR_REPORT，实际为 "
                        f"{value['md_report'].get('type')!r}（第 12 页：修复只消费 MD）")

    # ---------- output ----------

    def check_output(self, job_type, value, status, label, errors):
        if not isinstance(value, dict):
            errors.append(f"{label} 必须是对象")
            return
        if status in ("QUEUED", "RUNNING", "CANCELLED", "FAILED", "TIMED_OUT"):
            if value:
                errors.append(
                    f"{label} 在 {status} 状态必须为空对象，实际含: {', '.join(sorted(value))}")
            return
        # SUCCEEDED
        for i, f in enumerate(value.get("findings", [])):
            self.check_finding(f, f"{label}.findings[{i}]", errors)
        for i, a in enumerate(value.get("artifacts", [])):
            self.check_artifact(a, f"{label}.artifacts[{i}]", errors)
        for req in self.s.output_required.get(job_type, set()):
            if req not in value:
                errors.append(f"{label} 缺少 {job_type} 的输出必填字段: {req}")
        if job_type == "FULL_CHECK":
            counts = value.get("counts")
            self.check_counts(counts, f"{label}.counts", errors)
            self.check_counts_match_findings(
                counts, value.get("findings", []), label, errors)
            artifact_types = {
                a.get("type") for a in value.get("artifacts", [])
                if isinstance(a, dict)
            }
            required_types = {"ACTUAL_GRAPH", "DECLARED_GRAPH", "ERROR_REPORT"}
            missing_types = required_types - artifact_types
            if missing_types:
                errors.append(
                    f"{label}.artifacts 缺少 FULL_CHECK 必需产物: "
                    f"{', '.join(sorted(missing_types))}")
        if job_type == "INCREMENTAL_CHECK":
            for key in ("introduced", "resolved"):
                items = value.get(key)
                if not isinstance(items, list):
                    errors.append(f"{label}.{key} 必须是数组（第 22 页：新增/消除的发现）")
                else:
                    for i, f in enumerate(items):
                        self.check_finding(f, f"{label}.{key}[{i}]", errors)
            if "updated_graph" in value:
                self.check_artifact(value["updated_graph"], f"{label}.updated_graph", errors)
        if job_type == "REPAIR":
            if "patch" in value:
                self.check_artifact(value["patch"], f"{label}.patch", errors)
            ver = value.get("verification")
            if not isinstance(ver, dict) or set(ver) != {"build", "test", "recheck"}:
                errors.append(f"{label}.verification 必须恰好含 build/test/recheck（第 23 页）")
            elif not all(isinstance(ver[k], bool) for k in ver):
                errors.append(f"{label}.verification 三项必须是布尔值")
            self.check_str(value.get("declaration_style"), f"{label}.declaration_style", errors)

    # ---------- 状态矩阵 ----------

    def check_status_matrix(self, data, label, errors):
        status = data.get("status")
        error = data.get("error")
        output = data.get("output")
        http = data.get("http_status")

        if status in ("QUEUED", "RUNNING", "CANCELLED"):
            if error is not None:
                errors.append(f"{label} 状态矩阵违规：{status} 必须 error=null")
            if isinstance(output, dict) and output:
                errors.append(f"{label} 状态矩阵违规：{status} 的 output 必须为空")
        elif status == "SUCCEEDED":
            if error is not None:
                errors.append(
                    f"{label} 状态矩阵违规：SUCCEEDED 必须 error=null。检出 MD 属正常分析结果，"
                    f"应写 output.findings 而不是 error（第 8、9 页）")
        elif status in ("FAILED", "TIMED_OUT"):
            self.check_error(error, f"{label}.error", errors)
            if isinstance(output, dict) and output:
                errors.append(f"{label} 状态矩阵违规：{status} 的 output 必须为空")

        if "http_status" in data:
            if status != "QUEUED":
                errors.append(f"{label} 状态矩阵违规：http_status 只允许出现在 QUEUED 受理响应")
            elif http != 202:
                errors.append(f"{label} 状态矩阵违规：受理响应的 http_status 必须是 202，实际 {http!r}")

    # ---------- 顶层 ----------

    def validate(self, data, name="<doc>"):
        errors: list[str] = []
        if not isinstance(data, dict):
            return [f"{name}: 顶层必须是 JSON 对象"]

        # 下划线开头的键是给人看的注解（如 _note），不属于线上载荷，校验前剥离。
        data = {k: v for k, v in data.items() if not k.startswith("_")}

        kind = data.get("kind")
        if kind not in KINDS:
            return [f"{name}: kind 非法: {kind!r}，必须是 {'/'.join(KINDS)}"]

        allowed = self.s.envelope_fields[kind]
        required = self.s.envelope_required[kind]
        missing = required - set(data)
        if missing:
            errors.append(f"{name} 缺少 {kind} 必填字段: {', '.join(sorted(missing))}")
        unknown = set(data) - allowed
        if unknown:
            errors.append(f"{name} 含 {kind} 未定义字段（顶层信封已冻结）: {', '.join(sorted(unknown))}")
        if data.get("schema_version") != self.s.schema_version:
            errors.append(
                f"{name} schema_version 必须是 {self.s.schema_version}，实际 "
                f"{data.get('schema_version')!r}")

        job_type = data.get("job_type")
        if kind in ("create_request", "job"):
            if job_type not in self.s.job_types:
                errors.append(
                    f"{name} job_type 非法: {job_type!r}，必须是 "
                    f"{'/'.join(sorted(self.s.job_types))}")

        if kind == "create_request":
            self.check_pattern(data.get("trace_id"), f"{name}.trace_id", errors,
                               self.s.trace_id_re, "trace_id")
            self.check_str(data.get("idempotency_key"), f"{name}.idempotency_key", errors)
            if job_type in self.s.job_types:
                self.check_input(job_type, data.get("input"), f"{name}.input", errors)

        elif kind == "job":
            self.check_pattern(data.get("job_id"), f"{name}.job_id", errors,
                               self.s.job_id_re, "job_id")
            self.check_pattern(data.get("trace_id"), f"{name}.trace_id", errors,
                               self.s.trace_id_re, "trace_id")
            if data.get("status") not in self.s.statuses:
                errors.append(
                    f"{name} status 非法: {data.get('status')!r}，必须是 "
                    f"{'/'.join(sorted(self.s.statuses))}（第 8 页；注意课程规范用 QUEUED 而非 PENDING）")
            self.check_execution(data.get("execution"), f"{name}.execution", errors)
            if job_type in self.s.job_types:
                self.check_input(job_type, data.get("input"), f"{name}.input", errors)
                self.check_output(job_type, data.get("output"), data.get("status"),
                                  f"{name}.output", errors)
            self.check_status_matrix(data, name, errors)

        elif kind == "artifact_record":
            self.check_artifact(data, name, errors, allow_kind=True)
        else:
            self.check_artifact_body(kind, data, name, errors)

        return [f"{name}: {e}" if not e.startswith(name) else e for e in errors]


def load_schema(path: Path = SCHEMA_PATH) -> Schema:
    with path.open(encoding="utf-8") as fh:
        return Schema(json.load(fh))


def check_coverage(validator: Validator) -> list[str]:
    """第 25 页检查 01：四类请求与响应都要被覆盖；六种状态都要有样例。"""
    errors = []
    docs = []
    for path in sorted(SAMPLES.glob("*.json")):
        with path.open(encoding="utf-8") as fh:
            docs.append((path.name, json.load(fh)))

    requests = {jt for n, d in docs if d.get("kind") == "create_request"
                for jt in [d.get("job_type")]}
    responses = {jt for n, d in docs if d.get("kind") == "job" and d.get("status") == "SUCCEEDED"
                 for jt in [d.get("job_type")]}
    for jt in sorted(validator.s.job_types):
        if jt not in requests:
            errors.append(f"缺少 {jt} 的请求样例（第 25 页检查 01 要求覆盖四类请求）")
        if jt not in responses:
            errors.append(f"缺少 {jt} 的成功响应样例（第 25 页检查 01 要求覆盖四类响应）")

    seen_status = {d.get("status") for n, d in docs if d.get("kind") == "job"}
    for st in sorted(validator.s.statuses):
        if st not in seen_status:
            errors.append(f"缺少 status={st} 的 Job 样例（第 8 页状态需可表达）")

    if not any(d.get("kind") == "artifact_record" for n, d in docs):
        errors.append("缺少独立的 artifact_record 样例（第 24 页）")
    return errors


def run(paths: list[Path] | None = None) -> list[str]:
    validator = Validator(load_schema())
    errors: list[str] = []

    if paths:
        for path in paths:
            with path.open(encoding="utf-8") as fh:
                errors.extend(validator.validate(json.load(fh), path.name))
        return errors

    if not SAMPLES.is_dir():
        return [f"样例目录不存在: {SAMPLES}"]

    for path in sorted(SAMPLES.glob("*.json")):
        with path.open(encoding="utf-8") as fh:
            errors.extend(validator.validate(json.load(fh), path.name))

    invalid_dir = SAMPLES / "invalid"
    if invalid_dir.is_dir():
        for path in sorted(invalid_dir.glob("*.json")):
            with path.open(encoding="utf-8") as fh:
                data = json.load(fh)
            expected = data.pop("expected_error", None)
            found = validator.validate(data, path.name)
            if not found:
                errors.append(f"{path.name}: 负例竟然通过了校验，说明契约有漏洞")
                continue
            if not _s(expected):
                errors.append(f"{path.name}: 负例缺少 expected_error 说明")
                continue
            if not any(expected in item for item in found):
                errors.append(
                    f"{path.name}: 被拒原因与 expected_error 不符\n"
                    f"    期望包含: {expected}\n    实际产出: {'; '.join(found)}")

    errors.extend(check_coverage(validator))
    return errors


def main(argv: list[str]) -> int:
    paths = [Path(a) for a in argv[1:]] or None
    problems = run(paths)
    if problems:
        print("校验未通过：")
        for p in problems:
            print("  - " + p)
        return 1
    print("A09/B09 公共契约校验通过："
          "四类请求与响应、六种状态、artifact 元数据/本体与全部负例均符合 "
          "task.schema.json。")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
