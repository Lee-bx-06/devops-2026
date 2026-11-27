"""B2 E11: alternate Make declarations and stale MD input."""

import tempfile
import unittest
from pathlib import Path

from lab import commit, fixture, patch, scan, validate


class B2E11Cases(unittest.TestCase):
    def make_target(self, root, style):
        project = root / style
        fixture(project, style=style)
        main = project / 'main.c'
        main.write_text('#include "extra.h"\n' + main.read_text())
        commit(project, 'Add an undeclared local include')
        return project

    def test_macro_and_mixed_repairs(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            for style in ('macro', 'mixed'):
                with self.subTest(style=style):
                    project = self.make_target(root, style)
                    report = scan(project)
                    diff, edits = patch(project, report)
                    self.assertTrue(any(e['dependency'] == 'extra.h' for e in edits))
                    patchfile = root / (style + '.patch')
                    patchfile.write_text(diff)
                    verdict = validate(project, patchfile, root / (style + '-validation'))
                    self.assertTrue(verdict['accepted'], verdict)
                    makefile = (project / 'Makefile').read_text()
                    expected = ('DEPS = main.c unused.h config.h extra.h' if style == 'macro'
                                else 'main.o: main.c $(HEADERS) config.h extra.h')
                    self.assertIn(expected, makefile)
                    self.assertFalse(any(f['type'] == 'MISSING' for f in scan(project)['findings']))

    def test_stale_report_preserves_makefile(self):
        with tempfile.TemporaryDirectory() as temporary:
            project = self.make_target(Path(temporary), 'macro')
            report = scan(project)
            before = (project / 'Makefile').read_bytes()
            report['commit'] = '0' * 40
            with self.assertRaisesRegex(ValueError, 'STALE_REPORT'):
                patch(project, report)
            self.assertEqual((project / 'Makefile').read_bytes(), before)


if __name__ == '__main__':
    unittest.main()
