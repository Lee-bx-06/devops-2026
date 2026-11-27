"""Reconstruct the team's published E3 C0/C1 source snapshots as Git commits.

The source paths and original repository commit are recorded in dataset.json.
This dataset is separate from the course-generated integration sample.
"""

import shutil
from pathlib import Path

from b2_real import scan_real
from lab import commit, run
from pipeline import ROOT, save


def main():
    root = ROOT / 'data/b2-real-project'
    if root.exists():
        raise SystemExit('data/b2-real-project already exists; preserve the prior run')
    source = ROOT / 'e3/fixtures/commits'
    for revision in ('C0', 'C1'):
        if not (source / revision / 'Makefile').is_file():
            raise SystemExit(f'Missing team E3 source snapshot {revision}')
    project = root / 'repo'
    project.mkdir(parents=True)
    for path in (source / 'C0').iterdir():
        if path.is_file():
            shutil.copy2(path, project / path.name)
    broken = ('FROM python:3.13-slim\nWORKDIR /work\n'
              'COPY main.c config.h feature.h Makefile ./\n'
              'RUN make app\nCMD ["./app"]\n')
    (project / 'Dockerfile.broken').write_text(broken)
    (project / '.gitignore').write_text('*.o\napp\n')
    run(['git', 'init', '-b', 'main'], project)
    run(['git', 'config', 'user.name', '241250053'], project)
    run(['git', 'config', 'user.email', 'fixture@localhost'], project)
    base = commit(project, 'Import team E3 C0 published snapshot')
    for path in (source / 'C1').iterdir():
        if path.is_file():
            shutil.copy2(path, project / path.name)
    target = commit(project, 'Import team E3 C1 feature-header change')
    candidate = broken.replace(
        'FROM python:3.13-slim',
        'FROM python:3.13-slim@sha256:70729b46c69b4f1e97c4822c1af3df53a1476cf5ddc6c087c0c10bc3a5678c2f',
    ).replace(
        'RUN make app',
        'RUN apt-get update && apt-get install -y --no-install-recommends build-essential && rm -rf /var/lib/apt/lists/*\nRUN make app',
    )
    (root / 'candidate.Dockerfile').write_text(candidate)
    fixed = scan_real(project)
    save(root / 'fixed-md.json', {
        'schema_version': 'e11e12-1', 'kind': 'fixed-md',
        'status': 'SUCCEEDED', 'commit': target, 'data': fixed,
    })
    for mode in ('e11-b', 'e12'):
        save(root / (mode + '.json'), {
            'mode': mode, 'profile': 'E3_SINGLE_SOURCE',
            'repo': str(project), 'base': base, 'target': target,
            'candidate': str(root / 'candidate.Dockerfile'),
            'fixed_report': str(root / 'fixed-md.json'),
            'expected_output': '12', 'build_timeout': 600,
        })
    save(root / 'dataset.json', {
        'source_repo': 'https://github.com/Lee-bx-06/devops-2026',
        'source_commit': 'de31c63b96d969d5c71da1d172b0786d9b8a351a',
        'source_paths': ['e3/fixtures/commits/C0', 'e3/fixtures/commits/C1'],
        'adaptation': 'Published team source snapshots reconstructed as two local Git commits; no original source lines changed',
        'base_commit': base, 'target_commit': target,
        'candidate_source': 'Pinned base and dependency-install replay adapted to the team E3 single-source C/Make project',
        'expected_output': '12',
    })
    print(root)


if __name__ == '__main__':
    main()
