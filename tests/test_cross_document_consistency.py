"""跨文档一致性守卫。

`tools/validate.py` 是**单文档**校验器，它看不出「同一个 artifact 在两个文件里
被描述成不同样子」这类问题。这正是 `artifact-full09-error-report` 的
`configuration_id` 曾在 5 个样例里出现两种取值、而 `make check` 全绿三天的原因：
A2 把 DRAFT → FULL_CHECK 那半条链迁到了新值，FULL_CHECK → MDFixer 那半没动。

本文件把「交接链两端必须逐字一致」变成断言。第 5 页整页讲的就是这件事
（发送方提供什么、接收方检查什么），只是课件没有要求它可执行。
"""
import importlib.util
import json
import pathlib
import unittest

ROOT = pathlib.Path(__file__).resolve().parents[1]
SAMPLES = ROOT / "docs" / "interfaces" / "samples"

_spec = importlib.util.spec_from_file_location("validate", ROOT / "tools" / "validate.py")
validate = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(validate)


def load(name):
    with (SAMPLES / name).open(encoding="utf-8") as fh:
        return json.load(fh)


def all_positive_samples():
    for path in sorted(SAMPLES.glob("*.json")):
        yield path.name, json.loads(path.read_text(encoding="utf-8"))


def collect_artifact_records():
    """收集所有 artifact 记录，按 artifact_id 归组，记下各自出自哪个文件。"""
    found = {}

    def walk(node, name):
        if isinstance(node, dict):
            if "artifact_id" in node and "uri" in node:
                found.setdefault(node["artifact_id"], []).append((name, node))
            for value in node.values():
                walk(value, name)
        elif isinstance(node, list):
            for value in node:
                walk(value, name)

    for name, doc in all_positive_samples():
        walk(doc, name)
    return found


# 规范环境由 DRAFT 的成功输出定义（第 20、21 页：下游消费 DRAFT 产出的环境）
CANONICAL_ENV = load("draft.job-succeeded.json")["output"]["environment"]
CHAIN_COMMIT = load("draft.job-succeeded.json")["input"]["repository"]["commit"]

# 环境准备失败的场景合法地使用另一套（坏）环境，按错误码排除，不按文件名排除。
ENV_FAILURE_CODES = {"ENV_3002"}

# 已知偏差登记表：文件名 -> (负责人, 原因)。
# 守卫只拦「表外的新违规」，不强制本表收缩，免得 A1 的测试卡住别人的 PR。
# 本表的收缩记在 docs/BACKLOG.md。
KNOWN_ENV_DEVIATIONS = {
    # A3 的 PR #8 迁移了前两个；后两个在该 PR 上仍是旧值，需 A3 补齐。
    "incremental-check.request.json": ("A3", "PR #8 已迁移，待合并"),
    "incremental-check.job-succeeded.json": ("A3", "PR #8 已迁移，待合并"),
    "job.running.json": ("A3", "PR #8 未迁移，仍是 cc-MODE0 + tag 形式镜像"),
    "job.baseline-mismatch-failed.json": ("A3", "PR #8 未迁移，仍是 cc-MODE0 + tag 形式镜像"),
    # A2 的这个样例用了 iter4 tag 而非 DRAFT 产出的 digest，但 configuration_id
    # 与规范值相同。按 A2 自己写的 $defs.configuration_id 定义（「只随基础镜像、
    # 工具链、依赖集或构建参数变化」），镜像不同则 configuration_id 应当不同。
    # 二者必居其一，需 A2 裁定，A1 不擅自改 A2 的样例。
    "full-check.clean-project.json": ("A2", "image_uri 用 iter4 tag 而非 digest，但 configuration_id 与规范值相同"),
}


class TestArtifactRecordsAgreeAcrossDocuments(unittest.TestCase):
    def test_same_artifact_id_is_described_identically_everywhere(self):
        """同一个 artifact_id 在任何文件里都必须是同一条记录。

        记录不一致意味着下游按 sha256 校验时会失败，或者根本读到的
        不是它以为的那份文件。
        """
        records = collect_artifact_records()
        duplicated = {k: v for k, v in records.items() if len(v) > 1}
        self.assertTrue(duplicated, "样例中应存在跨文件复用的 artifact，否则本测试失去意义")
        for artifact_id, occurrences in sorted(duplicated.items()):
            with self.subTest(artifact_id=artifact_id):
                first_name, first = occurrences[0]
                for name, record in occurrences[1:]:
                    for field in ("uri", "type", "media_type", "producer_job_id",
                                  "commit", "configuration_id", "sha256"):
                        self.assertEqual(
                            first.get(field), record.get(field),
                            f"{artifact_id} 的 {field} 在 {first_name} 与 {name} 中不一致："
                            f"{first.get(field)!r} vs {record.get(field)!r}")

    def test_artifact_record_agrees_with_the_body_it_describes(self):
        """记录与它所描述的本体必须在 commit 与 configuration_id 上一致。"""
        pairs = [
            ("artifact.error-report.json", "artifact.error-report-body.json"),
        ]
        for record_name, body_name in pairs:
            with self.subTest(record=record_name):
                record = load(record_name)
                body = load(body_name)
                self.assertEqual(record["commit"], body["commit"],
                                 f"{record_name} 与 {body_name} 的 commit 不一致")
                self.assertEqual(record["configuration_id"], body["configuration_id"],
                                 f"{record_name} 与 {body_name} 的 configuration_id 不一致")


class TestRepairConsumesWhatFullCheckActuallyProduced(unittest.TestCase):
    """第 5 页「修复交接」：接收方要能核对报告属于当前源码版本。"""

    def test_md_report_matches_the_producer_record_field_by_field(self):
        full_check = load("full-check.job-succeeded.json")
        produced = [a for a in full_check["output"]["artifacts"]
                    if a["type"] == "ERROR_REPORT"]
        self.assertEqual(len(produced), 1, "FULL_CHECK 成功样例应恰好产出一份 ERROR_REPORT")
        produced = produced[0]

        for consumer_name in ("repair.request.json", "repair.job-succeeded.json",
                              "job.cancelled.json"):
            with self.subTest(consumer=consumer_name):
                consumed = load(consumer_name)["input"]["md_report"]
                self.assertEqual(consumed["artifact_id"], produced["artifact_id"])
                for field in ("uri", "media_type", "producer_job_id", "commit",
                              "configuration_id", "sha256"):
                    self.assertEqual(
                        consumed.get(field), produced.get(field),
                        f"{consumer_name} 的 md_report.{field} 与生产方 "
                        f"full-check.job-succeeded.json 不一致")

    def test_md_report_commit_equals_repair_repository_commit(self):
        """B3 的 ADR-009 判据：md_report.commit 必须等于 repository.commit。"""
        for name in ("repair.request.json", "repair.job-succeeded.json"):
            with self.subTest(sample=name):
                doc = load(name)
                self.assertEqual(doc["input"]["md_report"]["commit"],
                                 doc["input"]["repository"]["commit"])

    def test_md_report_configuration_matches_environment(self):
        """B3 的 ADR-009 判据：md_report.configuration_id 必须等于 environment.configuration_id。"""
        for name in ("repair.request.json", "repair.job-succeeded.json"):
            with self.subTest(sample=name):
                doc = load(name)
                self.assertEqual(doc["input"]["md_report"]["configuration_id"],
                                 doc["input"]["environment"]["configuration_id"])


class TestEnvironmentChainIsConsistent(unittest.TestCase):
    """同一个 commit 的检测/修复任务必须用 DRAFT 为该 commit 产出的那套环境。"""

    def _violations(self):
        bad = set()
        for name, doc in all_positive_samples():
            if doc.get("kind") != "job":
                continue
            if doc.get("job_type") not in ("FULL_CHECK", "INCREMENTAL_CHECK", "REPAIR"):
                continue
            repo = (doc.get("input") or {}).get("repository") or {}
            if repo.get("commit") != CHAIN_COMMIT:
                continue
            error = doc.get("error") or {}
            if error.get("code") in ENV_FAILURE_CODES:
                continue  # 环境准备失败的场景，合法地使用另一套环境
            env = (doc.get("input") or {}).get("environment")
            if env is not None and env != CANONICAL_ENV:
                bad.add(name)
        return bad

    def test_no_new_environment_drift(self):
        """不得出现登记表之外的新违规。

        这里用**子集**而不是相等断言，是刻意的：若要求完全相等，A3 的 PR #8
        只迁移了四个文件中的两个，合并时会因登记表未同步而失败——那等于用
        A1 的守卫去卡 A3 的进度。子集断言只拦「新增的不一致」，
        登记表的收缩由 `BACKLOG.md` 追踪。
        """
        unexpected = self._violations() - set(KNOWN_ENV_DEVIATIONS)
        self.assertEqual(
            unexpected, set(),
            f"以下样例的 environment 与 DRAFT 为同一 commit 产出的规范环境不一致，"
            f"且不在 KNOWN_ENV_DEVIATIONS 登记表内：{sorted(unexpected)}")


class TestNoStaleValuesRemain(unittest.TestCase):
    def test_a1_owned_samples_no_longer_use_the_retired_configuration_id(self):
        """`cc-MODE0` 是 A1 初版照抄第 22 页的取值，已被 A2/B2 的规范值取代。

        A3 的四个文件仍在迁移中，故只断言 A1 负责的文件。
        """
        retired = "cc-MODE0"
        for name, doc in all_positive_samples():
            if name in KNOWN_ENV_DEVIATIONS:
                continue
            with self.subTest(sample=name):
                self.assertNotIn(retired, json.dumps(doc),
                                 f"{name} 仍在使用已退役的 configuration_id {retired}")


if __name__ == "__main__":
    unittest.main(verbosity=2)
