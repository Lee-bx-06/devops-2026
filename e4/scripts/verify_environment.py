#!/usr/bin/env python3
"""Offline E4 configuration checks and raw evidence comparison (stdlib only).

A successful comparison is a consistency check, not a personal acceptance record.
"""
import argparse
import hashlib
import json
import re
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
ARTIFACTS = ('env.json', 'build.log', 'image.json', 'toolchain.lock',
             'test.log', 'smoke.json', 'secret-scan.txt')


def sha256(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def locked_requirements(text):
    """Accept this project's exact pins + SHA-256 format; reject unlocked options."""
    result = {}
    text = re.sub(r'\\\s*\n', ' ', text)
    for line in text.splitlines():
        line = line.split('#', 1)[0].strip()
        if not line:
            continue
        match = re.fullmatch(r'([A-Za-z0-9_.-]+)==([^\s;]+)((?:\s+--hash=sha256:[0-9a-f]{64})+)', line)
        if not match:
            raise ValueError(f'unpinned/unhashed requirement: {line}')
        name, version = match.group(1, 2)
        name = re.sub(r'[-_.]+', '-', name).lower()
        if name in result:
            raise ValueError(f'duplicate requirement: {name}')
        result[name] = version
    if not result:
        raise ValueError('empty requirements lock')
    return result


def static_checks(root):
    dockerfile = (root / 'services/buildchecker/Dockerfile').read_text()
    compose = (root / 'compose.yaml').read_text()
    makefile = (root / 'Makefile').read_text()
    base = re.search(r'^ARG BASE_IMAGE=(\S+)$', dockerfile, re.M)
    if not base or not re.fullmatch(r'[^\s]+@sha256:[0-9a-f]{64}', base[1]):
        raise ValueError('base image must have a SHA-256 digest')
    if not re.search(r'^\s+platform: linux/amd64\s*(?:#.*)?$', compose, re.M):
        raise ValueError('A09 platform must be linux/amd64')
    for required in ('--require-hashes', '--only-binary=:all:', 'python3 -m pip check',
                     'pip freeze --all', "dpkg-query -W -f='${binary:Package}=${Version}\\n'"):
        if required not in dockerfile:
            raise ValueError(f'missing Dockerfile safeguard: {required}')
    if re.search(r"dpkg-query[^\n]+\\n'\s+\w", dockerfile):
        raise ValueError('dpkg inventory must include transitive packages')
    for required in ('-o pipefail', '.NOTPARALLEL:', '--platform linux/amd64'):
        if required not in makefile:
            raise ValueError(f'missing Makefile safeguard: {required}')
    for required in ('cpus: 2', 'mem_limit: 1g', 'pids_limit: 256', 'network_mode: none'):
        if required not in compose:
            raise ValueError(f'missing runtime limit: {required}')
    pins = locked_requirements((root / 'requirements-dev.lock').read_text())
    direct = {}
    for line in (root / 'requirements-dev.in').read_text().splitlines():
        line = line.split('#', 1)[0].strip()
        if line:
            name, version = line.split('==')
            direct[re.sub(r'[-_.]+', '-', name).lower()] = version
    if any(pins.get(k) != v for k, v in direct.items()):
        raise ValueError('direct requirements differ from lock')
    return {'base_image': base[1], 'platform': 'linux/amd64',
            'requirements_sha256': sha256(root / 'requirements-dev.lock'), 'pins': pins}


def record(root):
    config = static_checks(root)
    def git(*args):
        return subprocess.check_output(['git', '-C', str(root), *args], text=True).strip()
    return dict(config, source_commit=git('rev-parse', 'HEAD'),
                dirty=bool(git('status', '--porcelain', '--untracked-files=normal')))


def inventory(text):
    result = {}
    for line in text.splitlines():
        if not line.strip():
            continue
        key, sep, value = line.partition('=')
        if not sep or not value or key in result:
            raise ValueError(f'invalid/duplicate toolchain entry: {line}')
        result[key] = value
    if not result:
        raise ValueError('empty toolchain inventory')
    return result


def load_run(path, summary=None):
    for name in ARTIFACTS:
        if not (path / name).is_file() or not (path / name).stat().st_size:
            raise ValueError(f'missing/empty evidence: {path / name}')
    if summary:
        expected = summary['evidence_sha256']
        if set(expected) != set(ARTIFACTS):
            raise ValueError('leader manifest must cover all seven artifacts')
        for name in ARTIFACTS:
            if sha256(path / name) != expected[name]:
                raise ValueError(f'leader evidence SHA-256 mismatch: {name}')
    read_json = lambda name: json.loads((path / name).read_text())
    provenance = read_json('source.json') if (path / 'source.json').exists() else None
    if provenance is None and summary:
        provenance = {'source_commit': summary['source_commit'], 'dirty': False}
    if not provenance or not re.fullmatch(r'[0-9a-f]{40}', provenance.get('source_commit', '')):
        raise ValueError(f'missing source provenance: {path}')
    if summary and provenance['source_commit'] != summary['source_commit']:
        raise ValueError('source provenance differs from leader summary')
    if provenance.get('dirty') is not False:
        raise ValueError(f'dirty or unknown source: {path}')
    env, image, smoke = (read_json(n) for n in ('env.json', 'image.json', 'smoke.json'))
    if env.get('problems') != []:
        raise ValueError(f'environment check failed: {path}')
    if env.get('arch') != 'x86_64' or image.get('arch') != 'amd64':
        raise ValueError(f'platform differs from A09 linux/amd64: {path}')
    test_log = (path / 'test.log').read_text()
    if (not re.search(r'\b3 passed\b', test_log)
            or re.search(r'\b[1-9]\d* (?:failed|errors?)\b', test_log)):
        raise ValueError(f'expected three passing unit tests: {path}')
    if (smoke.get('passed') is not True or smoke.get('make_exit_code') != 0
            or smoke.get('app_output') != '1' or not smoke.get('config_h_opened')):
        raise ValueError(f'smoke acceptance failed: {path}')
    return {'source': provenance, 'toolchain': inventory((path / 'toolchain.lock').read_text()),
            'warnings': env.get('warnings', []), 'identity': env.get('git', {})}


def compare(left, right):
    differences = {}
    for field in ('source_commit', 'base_image', 'platform', 'requirements_sha256'):
        a, b = left['source'].get(field), right['source'].get(field)
        if a != b:
            differences[field] = {'baseline': a, 'candidate': b}
    a, b = left['toolchain'], right['toolchain']
    for key in sorted(a.keys() | b.keys()):
        if a.get(key) != b.get(key):
            differences[f'toolchain:{key}'] = {'baseline': a.get(key), 'candidate': b.get(key)}
    return differences


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest='command', required=True)
    sub.add_parser('static')
    rec = sub.add_parser('record')
    rec.add_argument('--out', type=Path, required=True)
    cmp = sub.add_parser('compare')
    cmp.add_argument('baseline', type=Path)
    cmp.add_argument('candidate', type=Path)
    cmp.add_argument('--leader-summary', type=Path,
                     help='Verify baseline seven file hashes and legacy source SHA')
    args = parser.parse_args()
    try:
        if args.command == 'static':
            result = static_checks(ROOT)
        elif args.command == 'record':
            result = record(ROOT)
            args.out.write_text(json.dumps(result, indent=2) + '\n')
        else:
            summary = json.loads(args.leader_summary.read_text()) if args.leader_summary else None
            left = load_run(args.baseline, summary)
            right = load_run(args.candidate)
            differences = compare(left, right)
            result = {'differences': differences, 'baseline_warnings': left['warnings'],
                      'candidate_warnings': right['warnings'], 'candidate_identity': right['identity'],
                      'note': 'Consistency only; inspect build/scan logs, fake-key checks and identity manually.'}
            print(json.dumps(result, ensure_ascii=False, indent=2))
            return 1 if differences else 0
        print(json.dumps(result, ensure_ascii=False, indent=2))
        return 0
    except (OSError, ValueError, KeyError, subprocess.CalledProcessError) as error:
        print(json.dumps({'error': str(error)}, ensure_ascii=False))
        return 2


if __name__ == '__main__':
    raise SystemExit(main())
