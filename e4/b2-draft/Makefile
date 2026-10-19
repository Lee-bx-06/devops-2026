PYTHON ?= python3
RUN_ID ?= $(shell date -u +%Y%m%dT%H%M%SZ)
WORK_DIR ?= work/$(RUN_ID)

.PHONY: all doctor build test smoke scan shell lock clean

all:
	$(PYTHON) scripts/e4.py all --work-dir "$(WORK_DIR)"

doctor:
	$(PYTHON) scripts/e4.py doctor --work-dir "$(WORK_DIR)"

build:
	$(PYTHON) scripts/e4.py build --work-dir "$(WORK_DIR)"

test:
	$(PYTHON) scripts/e4.py test --work-dir "$(WORK_DIR)"

smoke:
	$(PYTHON) scripts/e4.py smoke --work-dir "$(WORK_DIR)"

scan:
	$(PYTHON) scripts/e4.py scan --work-dir "$(WORK_DIR)"

shell:
	$(PYTHON) scripts/e4.py shell --work-dir "$(WORK_DIR)"

lock:
	docker run --rm --user "$$(id -u):$$(id -g)" -e HOME=/tmp -v "$$(pwd):/src" -w /src python:3.13-slim@sha256:70729b46c69b4f1e97c4822c1af3df53a1476cf5ddc6c087c0c10bc3a5678c2f sh -c 'python3 -m venv /tmp/uv-venv && /tmp/uv-venv/bin/pip install -q uv==0.12.19 && /tmp/uv-venv/bin/uv pip compile requirements-dev.in --generate-hashes --python-version 3.13 --python-platform linux -o requirements-dev.lock'

clean:
	$(PYTHON) scripts/e4.py clean --work-dir "$(WORK_DIR)"
