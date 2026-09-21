"""A2 BuildChecker / FULL_CHECK 契约的可执行检查。"""
import copy
import importlib.util
import json
import pathlib
import unittest

ROOT = pathlib.Path(__file__).resolve().parents[1]
SAMPLES = ROOT / "docs" / "interfaces" / "samples"

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


class TestFullCheckArtifactBodies(unittest.TestCase):
    def test_actual_declared_and_report_bodies_are_valid(self):
        for name in (
            "artifact.actual-graph.json",
            "artifact.declared-graph.json",
            "artifact.error-report-body.json",
        ):
            with self.subTest(sample=name):
                self.assertEqual(errors_of(load(name), name), [])

    def test_all_full_check_bodies_use_same_commit_and_configuration(self):
        docs = [
            load("artifact.actual-graph.json"),
            load("artifact.declared-graph.json"),
            load("artifact.error-report-body.json"),
        ]
        self.assertEqual({d["commit"] for d in docs}, {
            "9f8e7d6c5b4a39281706f5e4d3c2b1a098765432"})
        self.assertEqual({d["configuration_id"] for d in docs},
                         {"cc-gcc13-release-6f12a4c8"})

    def test_error_report_matches_inline_findings(self):
        job = load("full-check.job-succeeded.json")
        report = load("artifact.error-report-body.json")
        self.assertEqual(job["output"]["counts"], report["counts"])
        self.assertEqual(job["output"]["findings"], report["findings"])

    def test_actual_and_declared_graphs_explain_the_findings(self):
        actual = load("artifact.actual-graph.json")
        declared = load("artifact.declared-graph.json")

        actual_edges = {
            (target["target"], dep["path"])
            for target in actual["targets"]
            for dep in target["dependencies"]
        }
        declared_edges = {
            (target["target"], dep["path"])
            for target in declared["targets"]
            for dep in target["prerequisites"]
        }

        # MD：实际访问 config.h，但没有声明。
        self.assertIn(("main.o", "src/config.h"), actual_edges)
        self.assertNotIn(("main.o", "src/config.h"), declared_edges)

        # RD：声明 legacy.h，但实际构建没有访问。
        self.assertIn(("util.o", "src/legacy.h"), declared_edges)
        self.assertNotIn(("util.o", "src/legacy.h"), actual_edges)


class TestFullCheckCrossFieldRules(unittest.TestCase):
    def test_success_requires_three_core_artifacts(self):
        job = load("full-check.job-succeeded.json")
        types = {artifact["type"] for artifact in job["output"]["artifacts"]}
        self.assertTrue({"ACTUAL_GRAPH", "DECLARED_GRAPH", "ERROR_REPORT"} <= types)

    def test_zero_findings_is_a_valid_success(self):
        job = load("full-check.job-succeeded.json")
        clean = copy.deepcopy(job)
        clean["output"]["counts"] = {"missing": 0, "redundant": 0}
        clean["output"]["findings"] = []
        self.assertEqual(errors_of(clean, "clean-project.json"), [])

    def test_counts_cannot_disagree_with_findings(self):
        job = load("full-check.job-succeeded.json")
        job["output"]["counts"]["missing"] = 0
        found = errors_of(job, "counts-mismatch.json")
        self.assertTrue(any("counts.missing" in error for error in found), found)

    def test_missing_actual_graph_is_rejected(self):
        job = load("full-check.job-succeeded.json")
        job["output"]["artifacts"] = [
            artifact for artifact in job["output"]["artifacts"]
            if artifact["type"] != "ACTUAL_GRAPH"
        ]
        found = errors_of(job, "missing-graph.json")
        self.assertTrue(any("缺少 FULL_CHECK 必需产物" in error for error in found), found)


if __name__ == "__main__":
    unittest.main(verbosity=2)
