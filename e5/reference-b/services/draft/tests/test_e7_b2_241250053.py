import json
from pathlib import Path
import tempfile
from types import SimpleNamespace
import unittest
from unittest.mock import patch

from draft import autobuild as workflow


BASE = (
    "FROM python:3.13-slim\n"
    "WORKDIR /work\n"
    "COPY main.c Makefile ./\n"
    "RUN make\n"
    'CMD ["./hello"]\n'
)
PINNED_FROM = "FROM python:3.13-slim@sha256:" + "a" * 64
CANDIDATE = BASE.replace("FROM python:3.13-slim", PINNED_FROM).replace(
    "RUN make",
    "RUN apt-get update && apt-get install -y build-essential\nRUN make",
)


class B2E7InspectFailureTests(unittest.TestCase):
    def test_image_inspect_failure_stops_runtime_verification(self):
        calls = []

        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            fixture = root / "fixture"
            fixture.mkdir()
            (fixture / "Dockerfile.broken").write_text(BASE, encoding="utf-8")
            (fixture / "main.c").write_text("source", encoding="utf-8")
            candidate = root / "candidate.Dockerfile"
            candidate.write_text(CANDIDATE, encoding="utf-8")

            def fake_execute(argv, stdout, stderr, timeout):
                calls.append(argv)
                stdout_path = Path(stdout)
                stderr_path = Path(stderr)
                stdout_path.write_text("", encoding="utf-8")
                stderr_path.write_text("", encoding="utf-8")

                if argv[1] == "build":
                    if stdout_path.parent.name == "iter-01":
                        stderr_path.write_text(
                            "/bin/sh: 1: make: not found\n",
                            encoding="utf-8",
                        )
                        return 1
                    return 0
                if argv[1:3] == ["image", "inspect"]:
                    stderr_path.write_text(
                        "Error: image metadata unavailable\n",
                        encoding="utf-8",
                    )
                    return 1
                if argv[1] == "run":
                    self.fail("Runtime verification must not start after inspect failure")
                raise AssertionError(f"Unexpected command: {argv}")

            with (
                patch.object(workflow, "os", SimpleNamespace(name="posix")),
                patch.object(workflow, "execute", fake_execute),
            ):
                report = workflow.auto_build(
                    fixture,
                    candidate,
                    root / "output",
                    "hello E3",
                )

            saved = json.loads(
                (root / "output/result.json").read_text(encoding="utf-8")
            )

        self.assertEqual(saved, report)
        self.assertEqual(report["status"], "FAILED")
        self.assertEqual(report["error"], "Cannot inspect built image")
        self.assertEqual(report["attempts"][1]["build_exit_code"], 0)
        self.assertNotIn("image_id", report["attempts"][1])
        self.assertNotIn("verification", report)
        self.assertTrue(any(argv[1:3] == ["image", "inspect"] for argv in calls))
        self.assertFalse(any(argv[1] == "run" for argv in calls))


if __name__ == "__main__":
    unittest.main()
