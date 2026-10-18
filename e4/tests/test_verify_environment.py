"""Synthetic regression fixtures only; never personal/leader acceptance evidence."""
import importlib.util
import json
import os
from pathlib import Path
import shutil
import subprocess
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location('verify_environment', ROOT / 'scripts/verify_environment.py')
verify = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(verify)


class ConfigurationTests(unittest.TestCase):
    def test_repository_configuration(self):
        self.assertEqual(verify.static_checks(ROOT)['pins']['pytest'], '8.4.2')

    def test_reject_unpinned_unhashed_and_duplicate_requirements(self):
        for text in ('pytest>=8', 'pytest==8.4.2', '--extra-index-url https://example.invalid',
                     'pytest==8.4.2 --hash=sha256:123',
                     ('pytest==8.4.2 --hash=sha256:' + 'a' * 64 + '\n') * 2):
            with self.subTest(text=text), self.assertRaises(ValueError):
                verify.locked_requirements(text)

    def test_configuration_drift(self):
        mutations = [
            ('compose.yaml', 'platform: linux/amd64', 'platform: linux/arm64'),
            ('compose.yaml', 'mem_limit: 1g', 'mem_limit: 2g'),
            ('Makefile', '-o pipefail', ''),
            ('services/buildchecker/Dockerfile', '--require-hashes', ''),
            ('services/buildchecker/Dockerfile', "\\n' | LC_ALL=C sort", "\\n' gcc make"),
            ('requirements-dev.in', 'pytest==8.4.2', 'pytest==8.4.1'),
        ]
        for filename, old, new in mutations:
            with self.subTest(filename=filename, old=old), tempfile.TemporaryDirectory() as tmp:
                dest = Path(tmp)
                for name in ('compose.yaml', 'Makefile', 'requirements-dev.in',
                             'requirements-dev.lock', 'services/buildchecker/Dockerfile'):
                    target = dest / name
                    target.parent.mkdir(parents=True, exist_ok=True)
                    shutil.copyfile(ROOT / name, target)
                path = dest / filename
                text = path.read_text()
                self.assertIn(old, text)
                path.write_text(text.replace(old, new))
                with self.assertRaises(ValueError):
                    verify.static_checks(dest)


class EvidenceTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.run_dir = Path(self.tmp.name)
        files = {
            'env.json': {'problems': [], 'arch': 'x86_64', 'warnings': ['2G host'],
                         'git': {'user.name': 'synthetic-test'}},
            'image.json': {'arch': 'amd64'},
            'smoke.json': {'passed': True, 'make_exit_code': 0, 'app_output': '1',
                           'config_h_opened': ['synthetic']},
            'source.json': {'source_commit': 'a' * 40, 'dirty': False},
        }
        for name, value in files.items():
            (self.run_dir / name).write_text(json.dumps(value))
        for name in ('build.log', 'secret-scan.txt'):
            (self.run_dir / name).write_text('synthetic test fixture\n')
        (self.run_dir / 'test.log').write_text('3 passed in 0.01s\n')
        (self.run_dir / 'toolchain.lock').write_text('gcc=14\narch=amd64\npip:pytest==8.4.2\n')
        self.manifest = {'source_commit': 'a' * 40, 'evidence_sha256': {
            name: verify.sha256(self.run_dir / name) for name in verify.ARTIFACTS}}

    def test_verify_legacy_manifest_and_detect_tampering(self):
        (self.run_dir / 'source.json').unlink()
        baseline = verify.load_run(self.run_dir, self.manifest)
        self.assertEqual(baseline['source']['source_commit'], 'a' * 40)
        (self.run_dir / 'toolchain.lock').write_text('gcc=15\n')
        with self.assertRaisesRegex(ValueError, 'SHA-256 mismatch'):
            verify.load_run(self.run_dir, self.manifest)

    def test_compare_versions_source_and_ignore_volatile_fields(self):
        left = verify.load_run(self.run_dir)
        right = verify.load_run(self.run_dir)
        right['warnings'] = []
        right['identity'] = {'user.name': 'another-synthetic-test'}
        self.assertEqual(verify.compare(left, right), {})
        right['source']['source_commit'] = 'b' * 40
        right['toolchain'] = dict(right['toolchain'], **{'gcc-14': '14.2.0-20'})
        differences = verify.compare(left, right)
        self.assertIn('source_commit', differences)
        self.assertIn('toolchain:gcc-14', differences)

    def test_reject_incomplete_or_failed_evidence(self):
        for filename, replacement in (
            ('smoke.json', '{"passed":true,"make_exit_code":0,"app_output":"2","config_h_opened":["x"]}'),
            ('env.json', '{"problems":["OOM"],"arch":"x86_64"}'),
            ('image.json', '{"arch":"arm64"}'),
            ('source.json', '{"source_commit":"' + 'a' * 40 + '","dirty":true}'),
            ('test.log', '2 passed, 1 failed'), ('test.log', '3 passed, 1 failed'),
            ('build.log', ''),
            ('toolchain.lock', 'gcc=14\ngcc=15\n'),
        ):
            path = self.run_dir / filename
            original = path.read_text()
            with self.subTest(filename=filename):
                path.write_text(replacement)
                with self.assertRaises(ValueError):
                    verify.load_run(self.run_dir)
                path.write_text(original)

    def test_public_summary_alone_is_insufficient(self):
        (self.run_dir / 'toolchain.lock').unlink()
        with self.assertRaisesRegex(ValueError, 'missing/empty evidence'):
            verify.load_run(self.run_dir, self.manifest)


class PipelineTests(unittest.TestCase):
    def run_build(self, fail_command='', fail_log=False):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            # Isolate Make recipes with fake local executables: no Docker or network.
            (root / 'Makefile').write_text((ROOT / 'Makefile').read_text())
            (root / '.env').touch()
            (root / 'bin').mkdir()
            (root / 'scripts').mkdir()
            (root / 'scripts/verify_environment.py').write_text('print("synthetic provenance stub")\n')
            (root / 'services/buildchecker').mkdir(parents=True)
            shutil.copyfile(ROOT / 'services/buildchecker/Dockerfile', root / 'services/buildchecker/Dockerfile')
            docker = root / 'bin/docker'
            docker.write_text('#!/bin/bash\n'
                              'if [[ "$*" == *"' + fail_command + '"* && -n "' + fail_command + '" ]]; then exit 42; fi\n'
                              'echo synthetic-fixture\n')
            docker.chmod(0o755)
            if fail_log:
                (root / 'work/test').mkdir(parents=True)
                (root / 'work/test/build.log').symlink_to('/dev/full')
            env = dict(os.environ, PATH=str(root / 'bin') + os.pathsep + os.environ['PATH'])
            return subprocess.run(['make', 'build', 'STUDENT_ID=synthetic', 'STAMP=test'],
                                  cwd=root, env=env, capture_output=True, text=True, timeout=15)

    def test_build_success(self):
        self.assertEqual(self.run_build().returncode, 0)

    def test_build_inspect_and_inventory_failures_propagate(self):
        for command in ('build --progress', 'image inspect', 'cat /opt/toolchain.lock'):
            with self.subTest(command=command):
                self.assertNotEqual(self.run_build(command).returncode, 0)

    @unittest.skipUnless(Path('/dev/full').exists(), 'requires Linux /dev/full')
    def test_evidence_write_failure_propagates(self):
        self.assertNotEqual(self.run_build(fail_log=True).returncode, 0)


if __name__ == '__main__':
    unittest.main()
