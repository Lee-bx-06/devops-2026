"""A3 EChecker / INCREMENTAL_CHECK 契约的行为检查。"""
import copy
import hashlib
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
VALIDATOR = validate.Validator(SCHEMA)


def load(name):
    with (SAMPLES / name).open(encoding="utf-8") as stream:
        return json.load(stream)


def errors_of(document, name="mutated.json"):
    return VALIDATOR.validate(document, name)


class TestIncrementalBaseline(unittest.TestCase):
    def test_project_root_is_required_and_absolute(self):
        request = load("incremental-check.request.json")

        missing_root = copy.deepcopy(request)
        del missing_root["input"]["build"]["project_root"]
        missing_errors = errors_of(missing_root, "missing-project-root.json")
        self.assertTrue(
            any("project_root" in error for error in missing_errors),
            missing_errors,
        )

        relative_root = copy.deepcopy(request)
        relative_root["input"]["build"]["project_root"] = "."
        relative_errors = errors_of(relative_root, "relative-project-root.json")
        self.assertTrue(
            any("project_root" in error and "POSIX" in error for error in relative_errors),
            relative_errors,
        )

    def test_historical_error_report_is_required(self):
        request = load("incremental-check.request.json")
        self.assertIn("error_report_uri", request["input"]["baseline"])

        missing_report = copy.deepcopy(request)
        del missing_report["input"]["baseline"]["error_report_uri"]
        found = errors_of(missing_report, "missing-baseline-report.json")

        self.assertTrue(any("error_report_uri" in error for error in found), found)

    def test_baseline_matches_frozen_buildchecker_artifacts(self):
        request = load("incremental-check.request.json")
        actual_graph = load("artifact.actual-graph.json")
        error_report = load("artifact.error-report-body.json")
        baseline = request["input"]["baseline"]

        self.assertEqual(
            baseline["actual_graph_uri"],
            "artifact://pair09/job-full09/actual.json",
        )
        self.assertEqual(
            baseline["error_report_uri"],
            "artifact://pair09/job-full09/error-report.json",
        )
        self.assertEqual(baseline["commit"], actual_graph["commit"])
        self.assertEqual(baseline["commit"], error_report["commit"])
        self.assertEqual(
            baseline["configuration_id"], actual_graph["configuration_id"]
        )
        self.assertEqual(
            baseline["configuration_id"], error_report["configuration_id"]
        )
        self.assertEqual(
            request["input"]["environment"]["configuration_id"],
            baseline["configuration_id"],
        )
        self.assertEqual(
            request["input"]["build"]["project_root"],
            actual_graph["project_root"],
        )
        self.assertNotEqual(
            request["input"]["repository"]["commit"], baseline["commit"]
        )


class TestIncrementalResult(unittest.TestCase):
    def test_successful_job_preserves_the_accepted_request(self):
        request = load("incremental-check.request.json")
        job = load("incremental-check.job-succeeded.json")

        self.assertEqual(job["input"], request["input"])

    def test_introduced_and_resolved_are_exact_set_differences(self):
        baseline_report = load("artifact.error-report-body.json")
        job = load("incremental-check.job-succeeded.json")

        def identity(finding):
            return (
                finding["type"],
                finding["target"],
                finding["dependency"],
            )

        c0 = {identity(finding) for finding in baseline_report["findings"]}
        c1 = {identity(finding) for finding in job["output"]["findings"]}
        introduced = {
            identity(finding) for finding in job["output"]["introduced"]
        }
        resolved = {identity(finding) for finding in job["output"]["resolved"]}

        self.assertEqual(introduced, c1 - c0)
        self.assertEqual(resolved, c0 - c1)

        c0_commit = job["input"]["base_commit"]
        c1_commit = job["input"]["repository"]["commit"]
        self.assertTrue(
            all(finding["commit"] == c1_commit for finding in job["output"]["findings"])
        )
        self.assertTrue(
            all(finding["commit"] == c1_commit for finding in job["output"]["introduced"])
        )
        self.assertTrue(
            all(finding["commit"] == c0_commit for finding in job["output"]["resolved"])
        )

    def test_introduced_must_also_be_a_current_finding(self):
        job = load("incremental-check.job-succeeded.json")
        invalid = copy.deepcopy(job)
        invalid["output"]["introduced"][0]["dependency"] = "not-current.h"

        found = errors_of(invalid, "introduced-not-current.json")

        self.assertTrue(any("introduced" in error and "findings" in error for error in found), found)

    def test_resolved_must_not_still_be_a_current_finding(self):
        job = load("incremental-check.job-succeeded.json")
        invalid = copy.deepcopy(job)
        invalid["output"]["resolved"] = [
            copy.deepcopy(invalid["output"]["findings"][0])
        ]
        invalid["output"]["resolved"][0]["commit"] = invalid["input"]["base_commit"]

        found = errors_of(invalid, "resolved-still-current.json")

        self.assertTrue(any("resolved" in error and "findings" in error for error in found), found)

    def test_finding_commits_follow_c0_and_c1(self):
        job = load("incremental-check.job-succeeded.json")

        wrong_current = copy.deepcopy(job)
        wrong_current["output"]["findings"][0]["commit"] = wrong_current["input"]["base_commit"]
        current_errors = errors_of(wrong_current, "current-finding-on-c0.json")
        self.assertTrue(
            any("findings" in error and "C1" in error for error in current_errors),
            current_errors,
        )

        wrong_resolved = copy.deepcopy(job)
        wrong_resolved["output"]["resolved"][0]["commit"] = wrong_resolved["input"]["repository"]["commit"]
        resolved_errors = errors_of(wrong_resolved, "resolved-finding-on-c1.json")
        self.assertTrue(
            any("resolved" in error and "C0" in error for error in resolved_errors),
            resolved_errors,
        )

    def test_updated_graph_is_a_c1_artifact_and_is_listed(self):
        job = load("incremental-check.job-succeeded.json")
        updated = job["output"]["updated_graph"]

        self.assertEqual(updated["type"], "ACTUAL_GRAPH")
        self.assertEqual(updated["producer_job_id"], job["job_id"])
        self.assertEqual(updated["commit"], job["input"]["repository"]["commit"])
        self.assertEqual(
            updated["configuration_id"],
            job["input"]["environment"]["configuration_id"],
        )
        self.assertIn(updated, job["output"]["artifacts"])

    def test_validator_rejects_an_unusable_updated_graph(self):
        job = load("incremental-check.job-succeeded.json")
        mutations = {
            "wrong-type": ("type", "DECLARED_GRAPH"),
            "wrong-commit": ("commit", job["input"]["base_commit"]),
            "wrong-configuration": ("configuration_id", "cc-other"),
            "wrong-producer": ("producer_job_id", "job-other"),
        }

        for name, (field, value) in mutations.items():
            with self.subTest(name=name):
                invalid = copy.deepcopy(job)
                invalid["output"]["updated_graph"][field] = value
                found = errors_of(invalid, f"updated-graph-{name}.json")
                self.assertTrue(any("updated_graph" in error for error in found), found)

        missing_from_artifacts = copy.deepcopy(job)
        missing_from_artifacts["output"]["artifacts"] = [
            artifact for artifact in missing_from_artifacts["output"]["artifacts"]
            if artifact["type"] != "ACTUAL_GRAPH"
        ]
        found = errors_of(missing_from_artifacts, "updated-graph-not-listed.json")
        self.assertTrue(any("updated_graph" in error and "artifacts" in error for error in found), found)

    def test_updated_graph_body_can_be_the_next_baseline(self):
        job = load("incremental-check.job-succeeded.json")
        body = load("artifact.incremental-actual-graph.json")
        updated = job["output"]["updated_graph"]

        self.assertEqual(errors_of(body, "artifact.incremental-actual-graph.json"), [])
        self.assertEqual(body["commit"], updated["commit"])
        self.assertEqual(body["configuration_id"], updated["configuration_id"])
        self.assertEqual(body["project_root"], job["input"]["build"]["project_root"])
        self.assertEqual(body["commit"], job["input"]["repository"]["commit"])

        graph_path = SAMPLES / "artifact.incremental-actual-graph.json"
        self.assertEqual(updated["size_bytes"], graph_path.stat().st_size)
        self.assertEqual(updated["sha256"], hashlib.sha256(graph_path.read_bytes()).hexdigest())

    def test_current_error_report_is_the_b3_handoff(self):
        job = load("incremental-check.job-succeeded.json")
        report = load("artifact.incremental-error-report-body.json")

        self.assertEqual(report["commit"], job["input"]["repository"]["commit"])
        self.assertEqual(
            report["configuration_id"],
            job["input"]["environment"]["configuration_id"],
        )
        self.assertEqual(report["findings"], job["output"]["findings"])
        self.assertEqual(
            report["counts"],
            {
                "missing": sum(
                    finding["type"] == "MISSING" for finding in report["findings"]
                ),
                "redundant": sum(
                    finding["type"] == "REDUNDANT" for finding in report["findings"]
                ),
            },
        )
        report_record = next(
            artifact for artifact in job["output"]["artifacts"]
            if artifact["type"] == "ERROR_REPORT"
        )
        report_path = SAMPLES / "artifact.incremental-error-report-body.json"
        self.assertEqual(report_record["size_bytes"], report_path.stat().st_size)
        self.assertEqual(
            report_record["sha256"], hashlib.sha256(report_path.read_bytes()).hexdigest()
        )


if __name__ == "__main__":
    unittest.main(verbosity=2)
