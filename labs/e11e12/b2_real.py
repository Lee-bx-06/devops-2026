"""Adapter for the team's E3 single-source C/Make dependency baseline.

The original E8-E10 two-source profile remains unchanged. This adapter is
selected explicitly by the E11/E12 request and rejects other Make layouts.
"""

import re
import shutil
import subprocess
from pathlib import Path

from lab import run
from pipeline import save


def scan_real(project, old=None):
    makefile = (project / 'Makefile').read_text()
    source = re.search(r'^SOURCES\s*=\s*(.+)$', makefile, re.M)
    rule = re.search(r'^main\.o:\s*(.+)$', makefile, re.M)
    if not source or not rule or source.group(1).strip() != 'main.c':
        raise ValueError('UNSUPPORTED_RULE: expected E3 main.o and SOURCES=main.c')
    raw = rule.group(1).replace('$(SOURCES)', 'main.c')
    if '$' in raw or '%' in raw or '|' in raw:
        raise ValueError('UNSUPPORTED_DECLARATION')
    declared = sorted(set(raw.split()))
    output = run(['gcc', '-MM', '-MT', 'main.o', 'main.c'], project)
    actual = sorted(set(output.replace('\\\n', ' ').split(':', 1)[1].split()))
    findings = [
        {'type': kind, 'target': 'main.o', 'dependency': dependency}
        for kind, dependencies in (
            ('MISSING', set(actual) - set(declared)),
            ('REDUNDANT', set(declared) - set(actual)),
        )
        for dependency in sorted(dependencies)
    ]
    previous = {(f['type'], f['target'], f['dependency']) for f in old['findings']} if old else set()
    current = {(f['type'], f['target'], f['dependency']) for f in findings}
    return {
        'schema_version': 'e8e10-1', 'profile': 'E3_SINGLE_SOURCE',
        'commit': run(['git', 'rev-parse', 'HEAD'], project).strip(),
        'actual': {'main.o': actual}, 'declared': {'main.o': declared},
        'findings': findings, 'added': [list(f) for f in sorted(current - previous)],
        'resolved': [list(f) for f in sorted(previous - current)],
        'refreshed': ['main.o'], 'reused': [],
    }


def validate_real(project, patchfile, evidence, expected_output):
    """Apply a candidate in a disposable copy before touching the target copy."""
    expected = int(expected_output)
    evidence.mkdir(parents=True, exist_ok=False)
    before = (project / 'Makefile').read_bytes()
    sandbox = evidence / 'sandbox'
    shutil.copytree(project, sandbox, ignore=shutil.ignore_patterns('.git', '*.o', 'app'))
    run(['git', 'init', '-b', 'main'], sandbox)
    run(['git', 'config', 'user.name', '241250053'], sandbox)
    run(['git', 'config', 'user.email', 'fixture@localhost'], sandbox)
    run(['git', 'add', '.'], sandbox)
    run(['git', 'commit', '-m', 'Validation input'], sandbox)
    checks = {}
    error = None
    try:
        run(['git', 'apply', '--check', str(patchfile.resolve())], sandbox)
        checks['patch_applies'] = True
        run(['git', 'apply', str(patchfile.resolve())], sandbox)
        build_log = run(['make', 'clean'], sandbox) + run(['make', 'app'], sandbox)
        (evidence / 'build.log').write_text(build_log)
        checks['build'] = True
        checks['test'] = run(['./app'], sandbox).strip() == str(expected)
        config = sandbox / 'config.h'
        original = config.read_text()
        changed, count = re.subn(r'(?m)^(#define BASE )([0-9]+)$',
                                 lambda match: match[1] + str(int(match[2]) + 1), original)
        if count != 1:
            raise ValueError('UNSUPPORTED_CONFIG: expected one numeric BASE')
        config.write_text(changed)
        (evidence / 'incremental.log').write_text(run(['make', 'app'], sandbox))
        checks['header_change'] = run(['./app'], sandbox).strip() == str(expected + 1)
        recheck = scan_real(sandbox)
        save(evidence / 'recheck.json', recheck)
        checks['no_missing'] = not any(f['type'] == 'MISSING' for f in recheck['findings'])
    except (ValueError, OSError, subprocess.TimeoutExpired) as exc:
        error = str(exc)
    accepted = bool(checks) and all(checks.values()) and error is None
    if accepted:
        (project / 'Makefile').write_bytes((sandbox / 'Makefile').read_bytes())
    unchanged = (project / 'Makefile').read_bytes() == before
    result = {'accepted': accepted, 'checks': checks, 'error': error,
              'source_unchanged': unchanged, 'rollback': not accepted and unchanged}
    save(evidence / 'validation.json', result)
    return result
