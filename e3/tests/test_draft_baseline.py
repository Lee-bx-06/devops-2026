from __future__ import annotations

import importlib.util
import json
import re
import unittest
from pathlib import Path


E3_ROOT = Path(__file__).resolve().parents[1]
FIXTURE_ROOT = E3_ROOT / "fixtures" / "draft"
RUNNER_PATH = E3_ROOT / "scripts" / "run_draft_baseline.py"
SPEC = importlib.util.spec_from_file_location("run_draft_baseline", RUNNER_PATH)
assert SPEC and SPEC.loader
RUNNER = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(RUNNER)


class TestDraftBaseline(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.baseline = json.loads((FIXTURE_ROOT / "baseline.json").read_text(encoding="utf-8"))

    def test_contract_mapping_is_complete_and_non_overlapping(self) -> None:
        self.assertEqual(
            self.baseline["build"],
            {
                "clean_command": "make clean",
                "command": "make all",
                "verify_command": "make test",
                "project_root": "/workspace/project",
            },
        )
        self.assertNotRegex(self.baseline["build"]["clean_command"], r"&&|\|\||;")

    def test_base_image_is_immutable(self) -> None:
        base = self.baseline["environment"]["base_image"]
        self.assertRegex(base, r"@sha256:[0-9a-f]{64}$")
        self.assertNotIn(":latest", base)
        for name in ("Dockerfile.broken", "Dockerfile.reference"):
            first = (FIXTURE_ROOT / name).read_text(encoding="utf-8").splitlines()[0]
            self.assertEqual(first, f"FROM {base}")

    def test_configuration_id_is_deterministic_and_tracks_cflags(self) -> None:
        expected = RUNNER.configuration_id_for(self.baseline)
        self.assertEqual(expected, self.baseline["environment"]["configuration_id"])
        self.assertRegex(expected, r"^cc-gcc-release-[0-9a-f]{12}$")
        c1 = RUNNER.configuration_id_for(self.baseline, cflags="-O0")
        c2 = RUNNER.configuration_id_for(self.baseline, cflags="-O0 -DMODE=7")
        self.assertNotEqual(c1, c2)

    def test_broken_candidate_omits_toolchain(self) -> None:
        broken = (FIXTURE_ROOT / "Dockerfile.broken").read_text(encoding="utf-8")
        self.assertIn("RUN make all", broken)
        self.assertNotRegex(broken, r"apt-get|apk add|yum install")

    def test_reference_candidate_runs_clean_build_verify_in_order(self) -> None:
        reference = (FIXTURE_ROOT / "Dockerfile.reference").read_text(encoding="utf-8")
        for package in self.baseline["environment"]["packages"]:
            self.assertRegex(reference, rf"\b{re.escape(package)}\b")
        clean = reference.index("RUN make clean")
        build = reference.index("RUN make all")
        verify = reference.index("RUN make test")
        self.assertLess(clean, build)
        self.assertLess(build, verify)

    def test_makefile_exposes_expected_targets_and_output(self) -> None:
        makefile = (FIXTURE_ROOT / "Makefile").read_text(encoding="utf-8")
        source = (FIXTURE_ROOT / "main.c").read_text(encoding="utf-8")
        self.assertIn("all: $(TARGET)", makefile)
        self.assertRegex(makefile, r"(?m)^clean:")
        self.assertRegex(makefile, r"(?m)^test: \$\(TARGET\)")
        self.assertIn('puts("hello E3")', source)

    def test_runner_static_validation(self) -> None:
        loaded = RUNNER.load_and_validate_baseline()
        self.assertEqual(loaded, self.baseline)


if __name__ == "__main__":
    unittest.main()
