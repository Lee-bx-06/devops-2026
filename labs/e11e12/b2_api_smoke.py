"""B2 HTTP smoke: asynchronous E12, idempotency, conflict, artifact hash."""

import argparse
import hashlib
import json
import time
import urllib.error
import urllib.request
import uuid
from pathlib import Path


def get(url):
    with urllib.request.urlopen(url, timeout=30) as response:
        return json.load(response)


def post(url, body):
    payload = json.dumps(body).encode()
    request = urllib.request.Request(url, payload, {'Content-Type': 'application/json'})
    with urllib.request.urlopen(request, timeout=30) as response:
        return response.status, json.load(response)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--request', type=Path, required=True)
    parser.add_argument('--out', type=Path, required=True)
    parser.add_argument('--url', default='http://127.0.0.1:18081')
    args = parser.parse_args()
    request = json.loads(args.request.read_text())
    if request.get('mode') != 'e12':
        parser.error('B2 API smoke requires an E12 request')
    url = args.url.rstrip('/')
    health = get(url + '/health')
    key = 'b2-241250053-' + uuid.uuid4().hex
    envelope = {'idempotency_key': key, 'input': request}
    first_status, first = post(url + '/v1/jobs', envelope)
    second_status, second = post(url + '/v1/jobs', envelope)
    if first_status != 202 or second_status != 202 or first['job_id'] != second['job_id']:
        raise ValueError('Idempotent POST did not return the same job')
    changed = dict(request, target='0' * 40)
    try:
        post(url + '/v1/jobs', {'idempotency_key': key, 'input': changed})
    except urllib.error.HTTPError as exc:
        conflict = {'http_status': exc.code, 'body': json.load(exc)}
        if exc.code != 409:
            raise
    else:
        raise ValueError('Changed input was not rejected with HTTP 409')
    job = first['job_id']
    deadline = time.monotonic() + 600
    while time.monotonic() < deadline:
        state = get(f'{url}/v1/jobs/{job}')
        if state['status'] in ('SUCCEEDED', 'FAILED', 'TIMED_OUT'):
            break
        time.sleep(1)
    else:
        raise TimeoutError('E12 API job did not finish in ten minutes')
    result = get(f'{url}/v1/jobs/{job}/artifacts')
    artifact = next(a for a in result['artifacts']
                    if a['uri'].endswith('/candidate.patch'))
    with urllib.request.urlopen(f'{url}/v1/jobs/{job}/files/candidate.patch', timeout=30) as response:
        patch = response.read()
        header_hash = response.headers['X-Content-SHA256']
    calculated_hash = hashlib.sha256(patch).hexdigest()
    if calculated_hash != header_hash or calculated_hash != artifact['sha256']:
        raise ValueError('Downloaded patch hash differs from response or manifest')
    if result['status'] != 'SUCCEEDED':
        raise ValueError(f'E12 API job failed: {result.get("error")}')
    args.out.mkdir(parents=True, exist_ok=False)
    record = {
        'health': health, 'job_id': job, 'trace_id': result['trace_id'],
        'status': result['status'], 'base_commit': result['base_commit'],
        'target_commit': result['target_commit'],
        'stages': [stage['name'] for stage in result['stages']],
        'repeat_job_id': second['job_id'], 'conflict': conflict,
        'downloaded_patch_sha256': calculated_hash,
        'artifact_uri': artifact['uri'],
    }
    (args.out / 'api-record.json').write_text(json.dumps(record, indent=2) + '\n')
    (args.out / 'candidate.patch').write_bytes(patch)
    print(json.dumps(record, indent=2))


if __name__ == '__main__':
    main()
