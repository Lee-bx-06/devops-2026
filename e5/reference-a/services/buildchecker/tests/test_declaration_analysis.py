"""E6 A3: declaration_graph / analyze boundary tests."""
import tempfile
import unittest
from pathlib import Path

from buildchecker.fullcheck import analyze, declaration_graph


class TestDeclarationAnalysis(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.folder = Path(self.temp.name)
        self.root = "/course/project"
        self.write(
            "t.10",
            'execve("/usr/bin/make", ["make", "unit.o"], []) = 0\n'
            "clone(child_stack=NULL, flags=SIGCHLD) = 11\n",
        )
        self.write(
            "t.11",
            'execve("/usr/bin/cc", ["cc", "-c", "unit.c", "-o", "unit.o"], []) = 0\n'
            'openat(AT_FDCWD, "unit.c", O_RDONLY) = 3\n'
            'openat(AT_FDCWD, "needed.h", O_RDONLY) = 4\n'
            'openat(AT_FDCWD, "unit.o", O_WRONLY|O_CREAT|O_TRUNC, 0666) = 5\n',
        )

    def tearDown(self):
        self.temp.cleanup()

    def write(self, name, text):
        path = self.folder / name
        path.write_text(text, encoding="utf-8")
        return path

    def test_order_only_prerequisite_is_not_a_declared_dependency(self):
        db = self.write(
            "db.txt",
            "# Files\nunit.o: unit.c needed.h | build-dir\n"
            "# files hash-table stats:\n",
        )
        result = analyze(self.folder, db, self.root)
        declared = declaration_graph(db, self.root)

        self.assertEqual(result["findings"], [])
        self.assertEqual(declared["unit.o"]["order_only"], ["build-dir"])
        self.assertNotIn(
            "build-dir",
            {edge["dependency"] for edge in result["declared_graph"]},
        )
