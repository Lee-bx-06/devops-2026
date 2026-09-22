"""E2 第 25 页「接口约定的最小检查」的可执行版本。

四条检查里 01-03 是代码，04 是文字说明（见 docs/interfaces/errors.md），
但这里也给它一条可执行的断言：把 MD 写进 output.findings 合法，
把同一条 MD 写进 job.error 非法。
"""
import copy
import hashlib
import importlib.util
import json
import pathlib
import re
import unittest

ROOT = pathlib.Path(__file__).resolve().parents[1]
SAMPLES = ROOT / "docs" / "interfaces" / "samples"
ARTIFACTS = ROOT / "docs" / "interfaces" / "artifacts"

_spec = importlib.util.spec_from_file_location("validate", ROOT / "tools" / "validate.py")
validate = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(validate)

SCHEMA = validate.load_schema()
V = validate.Validator(SCHEMA)


def load(name):
    with (SAMPLES / name).open(encoding="utf-8") as fh:
        return json.load(fh)


def errors_of(doc, name="mutated.json"):
    return V.validate(doc, name)


class TestRepoFixtures(unittest.TestCase):
    def test_run_reports_no_problem(self):
        self.assertEqual(validate.run(), [])

    def test_all_positive_samples_valid(self):
        for path in sorted(SAMPLES.glob("*.json")):
            with self.subTest(sample=path.name):
                self.assertEqual(errors_of(json.loads(path.read_text(encoding="utf-8")), path.name), [])

    def test_all_negatives_rejected_for_the_stated_reason(self):
        negatives = sorted((SAMPLES / "invalid").glob("*.json"))
        self.assertGreaterEqual(len(negatives), 12)
        for path in negatives:
            with self.subTest(negative=path.name):
                data = json.loads(path.read_text(encoding="utf-8"))
                expected = data.pop("expected_error")
                data.pop("_note", None)
                found = errors_of(data, path.name)
                self.assertTrue(found, f"{path.name} 竟然通过了校验")
                self.assertTrue(
                    any(expected in item for item in found),
                    f"{path.name} 拒绝原因不含 {expected!r}：{found}")


class TestDocsDoNotRot(unittest.TestCase):
    """VALIDATION.md 第五节是样例数量的唯一来源，其余文档一律指向它。

    数量写死在多处必然腐烂（本仓库已发生过一次：三个 ADR 里的计数在 B2
    补样例后全部过时）。这里把它变成断言，让腐烂当场变红。
    """

    def test_counts_in_validation_md_match_the_files(self):
        text = (ROOT / "docs" / "VALIDATION.md").read_text(encoding="utf-8")
        pos = len(list(SAMPLES.glob("*.json")))
        neg = len(list((SAMPLES / "invalid").glob("*.json")))
        m_pos = re.search(r"正例\s*(\d+)\s*个", text)
        m_neg = re.search(r"负例\s*(\d+)\s*个", text)
        self.assertIsNotNone(m_pos, "VALIDATION.md 第五节应写明正例数量")
        self.assertIsNotNone(m_neg, "VALIDATION.md 第五节应写明负例数量")
        self.assertEqual(int(m_pos.group(1)), pos,
                         f"VALIDATION.md 写正例 {m_pos.group(1)} 个，实际 {pos} 个")
        self.assertEqual(int(m_neg.group(1)), neg,
                         f"VALIDATION.md 写负例 {m_neg.group(1)} 个，实际 {neg} 个")

    def test_test_count_in_validation_md_matches_reality(self):
        """README 与 VALIDATION.md 若写了测试项数，必须与实际一致。"""
        actual = sum(1 for _ in _iter_test_ids())
        for doc in ("README.md", "docs/VALIDATION.md"):
            text = (ROOT / doc).read_text(encoding="utf-8")
            for m in re.finditer(r"(\d+)\s*项单元测试", text):
                self.assertEqual(int(m.group(1)), actual,
                                 f"{doc} 写「{m.group(1)} 项单元测试」，实际 {actual} 项")


def _iter_test_ids():
    loader = unittest.TestLoader()
    suite = loader.discover(str(ROOT / "tests"))

    def walk(s):
        for item in s:
            if isinstance(item, unittest.TestSuite):
                yield from walk(item)
            else:
                yield item

    yield from walk(suite)


class TestSlide25Check01FourJobTypes(unittest.TestCase):
    """检查 01：四类请求与响应都能被同一份 schema 表达。"""

    def test_four_request_response_pairs_exist_and_validate(self):
        for jt in sorted(SCHEMA.job_types):
            with self.subTest(job_type=jt):
                slug = jt.lower().replace("_", "-")
                req = load(f"{slug}.request.json")
                res = load(f"{slug}.job-succeeded.json")
                self.assertEqual(req["job_type"], jt)
                self.assertEqual(res["job_type"], jt)
                self.assertEqual(errors_of(req, f"{slug}.request.json"), [])
                self.assertEqual(errors_of(res, f"{slug}.job-succeeded.json"), [])
                # 响应必须回显请求的 input，否则下游无法核对任务身份
                self.assertEqual(res["input"], req["input"])

    def test_all_six_statuses_expressible(self):
        seen = set()
        for path in sorted(SAMPLES.glob("job.*.json")):
            seen.add(json.loads(path.read_text(encoding="utf-8"))["status"])
        for path in sorted(SAMPLES.glob("*.job-succeeded.json")):
            seen.add(json.loads(path.read_text(encoding="utf-8"))["status"])
        self.assertEqual(seen, SCHEMA.statuses)


class TestSlide25Check02BadJobType(unittest.TestCase):
    """检查 02：将 job_type 改成 ABC，应被拒绝。"""

    def test_mutating_job_type_to_abc_is_rejected(self):
        for name in ("full-check.request.json", "full-check.job-succeeded.json"):
            with self.subTest(sample=name):
                doc = load(name)
                doc["job_type"] = "ABC"
                found = errors_of(doc, name)
                self.assertTrue(any("job_type 非法" in e for e in found), found)

    def test_every_non_enum_job_type_is_rejected(self):
        base = load("full-check.request.json")
        for bad in ("ABC", "full_check", "Draft", "", "FULL_CHECK "):
            with self.subTest(bad=bad):
                doc = dict(base, job_type=bad)
                self.assertTrue(any("job_type 非法" in e for e in errors_of(doc)))


class TestSlide25Check03MissingBaseline(unittest.TestCase):
    """检查 03：删除增量任务的 baseline，应被拒绝。"""

    def test_removing_baseline_is_rejected(self):
        doc = load("incremental-check.request.json")
        self.assertIn("baseline", doc["input"])
        del doc["input"]["baseline"]
        found = errors_of(doc, "incremental-check.request.json")
        self.assertTrue(any("baseline" in e for e in found), found)

    def test_empty_baseline_object_is_rejected(self):
        doc = load("incremental-check.request.json")
        doc["input"]["baseline"] = {}
        found = errors_of(doc, "incremental-check.request.json")
        self.assertTrue(any("baseline" in e for e in found), found)

    def test_baseline_missing_configuration_id_is_rejected(self):
        doc = load("incremental-check.request.json")
        del doc["input"]["baseline"]["configuration_id"]
        found = errors_of(doc, "incremental-check.request.json")
        self.assertTrue(any("configuration_id" in e for e in found), found)

    def test_baseline_commit_must_be_full_sha(self):
        doc = load("incremental-check.request.json")
        doc["input"]["baseline"]["commit"] = "a1b2c3d"
        found = errors_of(doc, "incremental-check.request.json")
        self.assertTrue(any("commit 格式不符" in e for e in found), found)

    def test_valid_baseline_still_passes(self):
        self.assertEqual(errors_of(load("incremental-check.request.json")), [])


class TestSlide25Check04MdIsNotExecutionFailure(unittest.TestCase):
    """检查 04：MD 是正常分析发现，不是工具执行失败。"""

    def test_succeeded_job_may_report_missing_dependency(self):
        doc = load("full-check.job-succeeded.json")
        self.assertEqual(doc["status"], "SUCCEEDED")
        self.assertIsNone(doc["error"])
        types = {f["type"] for f in doc["output"]["findings"]}
        self.assertIn("MISSING", types)
        self.assertEqual(errors_of(doc, "full-check.job-succeeded.json"), [])

    def test_same_finding_moved_into_error_is_rejected(self):
        doc = load("full-check.job-succeeded.json")
        finding = doc["output"]["findings"][0]
        doc["status"] = "FAILED"
        doc["output"] = {}
        doc["error"] = {"code": finding["type"], "message": finding["message"]}
        found = errors_of(doc, "mutated.json")
        self.assertTrue(any("error.code 非法" in e for e in found), found)

    def test_failed_job_cannot_carry_findings(self):
        doc = load("full-check.job-succeeded.json")
        doc["status"] = "FAILED"
        doc["error"] = {"code": "ANALYSIS_5001", "message": "分析器失败"}
        found = errors_of(doc, "mutated.json")
        self.assertTrue(any("output 必须为空" in e for e in found), found)

    def test_system_error_codes_are_accepted(self):
        for code in ("ENV_3002", "EXEC_4002", "ANALYSIS_5001", "ENV_3003", "EXEC_4001", "ANALYSIS_5002"):
            with self.subTest(code=code):
                doc = load("job.failed.json")
                doc["error"]["code"] = code
                self.assertEqual(errors_of(doc, "mutated.json"), [])

    def test_validation_codes_are_rejected_in_job_error(self):
        """B1 于 2026-09-21 在 errors.md 第二节限定：VALIDATION_2xxx 只出现在
        创建期 HTTP 4xx 响应体，不写入 job.error。schema 必须强制这条。"""
        for code in ("VALIDATION_2001", "VALIDATION_2002"):
            with self.subTest(code=code):
                doc = load("job.failed.json")
                doc["error"]["code"] = code
                found = errors_of(doc, "mutated.json")
                self.assertTrue(any("不得写入 job.error" in e for e in found), found)

    def test_schema_splits_the_two_code_namespaces(self):
        self.assertFalse(SCHEMA.job_error_code_re.match("VALIDATION_2001"))
        self.assertTrue(SCHEMA.request_error_code_re.match("VALIDATION_2001"))
        for code in ("ENV_3002", "EXEC_4002", "ANALYSIS_5001"):
            self.assertTrue(SCHEMA.job_error_code_re.match(code), code)
            self.assertFalse(SCHEMA.request_error_code_re.match(code), code)


class TestTransitionTiming(unittest.TestCase):
    """B1 在 endpoints.md「状态迁移」一节的规则，形式化为单文档计时约束（ADR-010）。"""

    def test_queued_must_not_have_started_or_finished(self):
        doc = load("job.accepted-queued.json")
        self.assertEqual(errors_of(doc, "job.accepted-queued.json"), [])
        doc["execution"]["started_at"] = "2026-09-20T09:20:03Z"
        self.assertTrue(any("QUEUED 尚未被执行器领取" in e for e in errors_of(doc)))

    def test_running_must_have_started_but_not_finished(self):
        doc = load("job.running.json")
        self.assertEqual(errors_of(doc, "job.running.json"), [])
        doc["execution"]["started_at"] = None
        self.assertTrue(any("QUEUED→RUNNING 必须写入" in e for e in errors_of(doc)))

    def test_non_terminal_must_not_have_finished_at(self):
        for name in ("job.accepted-queued.json", "job.running.json"):
            with self.subTest(sample=name):
                doc = load(name)
                doc["execution"]["finished_at"] = "2026-09-20T09:31:12Z"
                self.assertTrue(any("非终态" in e for e in errors_of(doc)))

    def test_succeeded_cannot_skip_running(self):
        doc = load("full-check.job-succeeded.json")
        doc["execution"]["started_at"] = None
        found = errors_of(doc)
        self.assertTrue(any("不得跳过 RUNNING" in e for e in found), found)

    def test_every_terminal_state_has_finished_at(self):
        for name in ("full-check.job-succeeded.json", "job.failed.json",
                     "job.timed-out.json", "job.cancelled.json",
                     "job.analysis-failed.json", "job.baseline-mismatch-failed.json"):
            with self.subTest(sample=name):
                doc = load(name)
                self.assertIsNotNone(doc["execution"]["finished_at"], name)
                self.assertEqual(errors_of(doc, name), [])
                doc["execution"]["finished_at"] = None
                self.assertTrue(any("终态" in e for e in errors_of(doc)))

    def test_failed_without_started_at_is_allowed(self):
        """B1 迁移表里的 QUEUED→FAILED（受理后环境准备失败）从未进入 RUNNING，
        因此 started_at 为 null 合法。这条正是解开他表内自相矛盾之处。"""
        doc = load("job.failed.json")
        doc["execution"]["started_at"] = None
        doc["execution"]["duration_ms"] = None
        doc["error"]["code"] = "ENV_3002"
        self.assertEqual(errors_of(doc, "mutated.json"), [])

    def test_cancelled_without_started_at_is_allowed(self):
        doc = load("job.cancelled.json")
        doc["execution"]["started_at"] = None
        self.assertEqual(errors_of(doc, "mutated.json"), [])


class TestBaselineConsistencyIsRuntimeNotContract(unittest.TestCase):
    """B1 在 endpoints.md 末尾要求 baseline 与请求的 commit / configuration_id 一致。

    按第 5 页，这一列是「接收方检查」，即 EChecker 在运行期做的事；ADR-005 也把
    语义真值划归运行期。所以契约校验器**故意不**强制它。本类把这层边界钉住，
    防止后来者误把它收紧成创建期拒绝。
    """

    def test_mismatched_baseline_commit_passes_the_validator(self):
        doc = load("job.baseline-mismatch-failed.json")
        self.assertNotEqual(doc["input"]["base_commit"], doc["input"]["baseline"]["commit"])
        self.assertEqual(errors_of(doc, "job.baseline-mismatch-failed.json"), [])

    def test_mismatched_configuration_id_passes_the_validator(self):
        doc = load("incremental-check.request.json")
        doc["input"]["baseline"]["configuration_id"] = "cc-MODE9"
        self.assertNotEqual(doc["input"]["baseline"]["configuration_id"],
                            doc["input"]["environment"]["configuration_id"])
        self.assertEqual(errors_of(doc, "mutated.json"), [])

    def test_baseline_shape_is_still_enforced(self):
        """不强制值相等，但字段必须齐全、格式必须合法——这条界线不能松。"""
        doc = load("incremental-check.request.json")
        del doc["input"]["baseline"]["configuration_id"]
        self.assertTrue(any("configuration_id" in e for e in errors_of(doc)))


class TestEnvelopeIsFrozen(unittest.TestCase):
    """第 26 页：顶层信封严格，input/output 内部可加字段。"""

    def test_extra_top_level_field_rejected(self):
        for name in ("full-check.request.json", "full-check.job-succeeded.json"):
            with self.subTest(sample=name):
                doc = load(name)
                doc["priority"] = "high"
                self.assertTrue(any("未定义字段" in e for e in errors_of(doc, name)))

    def test_service_may_extend_input_additively(self):
        doc = load("full-check.request.json")
        doc["input"]["a09_extension"] = {"note": "服务专属扩展属可兼容变化"}
        self.assertEqual(errors_of(doc, "full-check.request.json"), [])

    def test_create_request_must_not_carry_server_generated_fields(self):
        doc = load("full-check.request.json")
        doc["job_id"] = "job-full09"
        self.assertTrue(any("未定义字段" in e for e in errors_of(doc)))


class TestArtifactContract(unittest.TestCase):
    """第 24 页：产物记录必须可追溯、可核验、命名空间正确。"""

    def test_artifact_record_valid(self):
        self.assertEqual(errors_of(load("artifact.error-report.json"), "artifact.error-report.json"), [])

    def test_foreign_pair_namespace_rejected(self):
        doc = load("artifact.error-report.json")
        doc["uri"] = doc["uri"].replace("pair09", "pair01")
        self.assertTrue(any("artifact_uri" in e for e in errors_of(doc)))

    def test_missing_sha256_rejected(self):
        doc = load("artifact.error-report.json")
        del doc["sha256"]
        self.assertTrue(any("sha256" in e for e in errors_of(doc)))

    def test_repair_consumes_error_report_only(self):
        doc = load("repair.request.json")
        self.assertEqual(doc["input"]["md_report"]["type"], "ERROR_REPORT")
        doc["input"]["md_report"]["type"] = "ACTUAL_GRAPH"
        self.assertTrue(any("只消费 MD" in e for e in errors_of(doc)))


class TestA2B2DraftHandoff(unittest.TestCase):
    """A2/B2 约定：DRAFT 成功输出可不转换地交给 FULL_CHECK。"""

    def setUp(self):
        self.request = load("draft.request.json")
        self.succeeded = load("draft.job-succeeded.json")
        self.full_check = load("full-check.request.json")

    def test_only_one_canonical_draft_request_and_success_exist(self):
        draft_requests = []
        draft_successes = []
        for path in sorted(SAMPLES.glob("*.json")):
            doc = json.loads(path.read_text(encoding="utf-8"))
            if doc.get("job_type") != "DRAFT":
                continue
            if doc.get("kind") == "create_request":
                draft_requests.append(path.name)
            if doc.get("kind") == "job" and doc.get("status") == "SUCCEEDED":
                draft_successes.append(path.name)
        self.assertEqual(draft_requests, ["draft.request.json"])
        self.assertEqual(draft_successes, ["draft.job-succeeded.json"])

    def test_draft_output_maps_directly_to_full_check_input(self):
        output = self.succeeded["output"]
        full_input = self.full_check["input"]
        self.assertEqual(output["environment"], full_input["environment"])
        self.assertEqual(output["build"], full_input["build"])
        self.assertEqual(
            self.request["input"]["repository"], full_input["repository"])
        self.assertEqual(
            self.succeeded["input"]["repository"]["commit"],
            full_input["repository"]["commit"])
        self.assertEqual(self.succeeded["trace_id"], self.request["trace_id"])

    def test_draft_handoff_required_fields_are_enforced(self):
        mutations = (
            (("environment",), "environment"),
            (("environment", "configuration_id"), "configuration_id"),
            (("build", "command"), "command"),
            (("build", "clean_command"), "clean_command"),
            (("build", "verify_command"), "verify_command"),
            (("build", "project_root"), "project_root"),
        )
        for path, expected in mutations:
            with self.subTest(field=".".join(path)):
                doc = copy.deepcopy(self.succeeded)
                target = doc["output"]
                for key in path[:-1]:
                    target = target[key]
                del target[path[-1]]
                found = errors_of(doc, "draft-mutated.json")
                self.assertTrue(any(expected in item for item in found), found)

    def test_image_configuration_and_build_semantics(self):
        output = self.succeeded["output"]
        image_uri = output["environment"]["image_uri"]
        configuration_id = output["environment"]["configuration_id"]
        commit = self.succeeded["input"]["repository"]["commit"]
        self.assertRegex(image_uri, r"@sha256:[0-9a-f]{64}$")
        self.assertNotIn(":latest", image_uri)
        self.assertNotIn(commit, configuration_id)
        self.assertNotIn(commit[:8], configuration_id)
        self.assertNotIn(self.succeeded["job_id"], configuration_id)
        self.assertIsNone(re.fullmatch(
            r"[0-9a-f]{8}-[0-9a-f]{4}-[1-5][0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}",
            configuration_id, re.IGNORECASE))
        self.assertEqual(output["build"]["clean_command"], "make clean")
        self.assertEqual(output["build"]["command"], "make all")
        self.assertEqual(output["build"]["verify_command"], "make test")
        self.assertTrue(output["build"]["project_root"].startswith("/"))
        self.assertEqual(output["build_result"]["iterations"], len(output["rounds"]))

    def test_artifacts_match_environment_rounds_and_fixture_hashes(self):
        output = self.succeeded["output"]
        commit = self.succeeded["input"]["repository"]["commit"]
        configuration_id = output["environment"]["configuration_id"]
        artifacts = {item["uri"]: item for item in output["artifacts"]}
        self.assertIn("DOCKERFILE", {item["type"] for item in output["artifacts"]})
        for round_item in output["rounds"]:
            artifact = artifacts[round_item["log_uri"]]
            self.assertEqual(artifact["type"], "BUILD_LOG")
        for artifact in output["artifacts"]:
            self.assertEqual(artifact["commit"], commit)
            self.assertEqual(artifact["configuration_id"], configuration_id)
            name = artifact["uri"].rsplit("/", 1)[-1]
            fixture = ARTIFACTS / "job-draft09" / name
            self.assertTrue(fixture.is_file(), fixture)
            self.assertEqual(fixture.stat().st_size, artifact["size_bytes"])
            self.assertEqual(
                hashlib.sha256(fixture.read_bytes()).hexdigest(), artifact["sha256"])

    def test_validator_rejects_cross_field_mismatches(self):
        cases = []

        wrong_config = copy.deepcopy(self.succeeded)
        wrong_config["output"]["artifacts"][0]["configuration_id"] = "cc-other-deadbeef"
        cases.append((wrong_config, "configuration_id 必须与 environment 一致"))

        missing_log = copy.deepcopy(self.succeeded)
        missing_log["output"]["rounds"][0]["log_uri"] = (
            "artifact://pair09/job-draft09/missing.log")
        cases.append((missing_log, "没有对应记录"))

        floating_image = copy.deepcopy(self.succeeded)
        floating_image["output"]["environment"]["image_uri"] = (
            "registry.pair09.local/demo-make-project:latest")
        cases.append((floating_image, "禁止使用浮动标签"))

        overlapping_clean = copy.deepcopy(self.succeeded)
        overlapping_clean["output"]["build"]["clean_command"] = "make clean && make all"
        cases.append((overlapping_clean, "不得与构建命令串联"))

        relative_root = copy.deepcopy(self.succeeded)
        relative_root["output"]["build"]["project_root"] = "."
        cases.append((relative_root, "绝对 POSIX 路径"))

        for doc, expected in cases:
            with self.subTest(expected=expected):
                found = errors_of(doc, "draft-mutated.json")
                self.assertTrue(any(expected in item for item in found), found)

    def test_failed_timed_out_and_iteration_exhausted_paths(self):
        failed = load("draft.job-failed.json")
        timed_out = load("job.timed-out.json")
        self.assertEqual((failed["status"], failed["error"]["code"], failed["output"]),
                         ("FAILED", "ENV_3002", {}))
        self.assertIn("max_iterations", failed["error"]["message"])
        self.assertEqual(
            (timed_out["status"], timed_out["error"]["code"], timed_out["output"]),
            ("TIMED_OUT", "EXEC_4002", {}))
        self.assertEqual(errors_of(failed, "draft.job-failed.json"), [])
        self.assertEqual(errors_of(timed_out, "job.timed-out.json"), [])


class TestSchemaAndValidatorAgree(unittest.TestCase):
    """校验器从 schema 读取常量，二者不应漂移。"""

    def test_schema_declares_the_deck_enums(self):
        self.assertEqual(SCHEMA.job_types, {"DRAFT", "FULL_CHECK", "INCREMENTAL_CHECK", "REPAIR"})
        self.assertEqual(SCHEMA.statuses,
                         {"QUEUED", "RUNNING", "SUCCEEDED", "FAILED", "TIMED_OUT", "CANCELLED"})
        self.assertEqual(SCHEMA.finding_types, {"MISSING", "REDUNDANT"})
        self.assertEqual(SCHEMA.schema_version, "1.0.0")

    def test_every_job_type_has_an_input_definition(self):
        for jt in sorted(SCHEMA.job_types):
            with self.subTest(job_type=jt):
                self.assertTrue(SCHEMA.input_required[jt], f"{jt} 的 input 没有任何必填字段")

    def test_incremental_check_requires_baseline(self):
        self.assertIn("baseline", SCHEMA.input_required["INCREMENTAL_CHECK"])

    def test_schema_file_is_valid_json(self):
        with (ROOT / "docs" / "interfaces" / "task.schema.json").open(encoding="utf-8") as fh:
            json.load(fh)


if __name__ == "__main__":
    unittest.main(verbosity=2)
