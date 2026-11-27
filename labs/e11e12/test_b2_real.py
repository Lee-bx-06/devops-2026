"""B2 adapter check against the team's published E3 C1 source snapshot."""

import shutil
import tempfile
import unittest
from pathlib import Path

from b2_real import scan_real, validate_real
from lab import patch, run
from pipeline import ROOT


class TeamE3Adapter(unittest.TestCase):
    def test_real_source_missing_feature_and_repair(self):
        source = ROOT / 'e3/fixtures/commits/C1'
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            project = root / 'project'
            shutil.copytree(source, project)
            run(['git', 'init', '-b', 'main'], project)
            run(['git', 'config', 'user.name', '241250053'], project)
            run(['git', 'config', 'user.email', 'fixture@localhost'], project)
            run(['git', 'add', '.'], project)
            run(['git', 'commit', '-m', 'Team E3 C1 snapshot'], project)
            report = scan_real(project)
            self.assertIn({'type': 'MISSING', 'target': 'main.o',
                           'dependency': 'feature.h'}, report['findings'])
            diff, edits = patch(project, report)
            self.assertTrue(any(edit['dependency'] == 'feature.h' for edit in edits))
            patchfile = root / 'candidate.patch'
            patchfile.write_text(diff)
            verdict = validate_real(project, patchfile, root / 'validation', '12')
            self.assertTrue(verdict['accepted'], verdict)
            self.assertFalse(any(f['type'] == 'MISSING'
                                 for f in scan_real(project)['findings']))


if __name__ == '__main__':
    unittest.main()
