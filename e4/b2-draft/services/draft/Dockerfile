ARG DOCKER_CLI_IMAGE=docker:28.5.1-cli@sha256:9190b0613792e658a7783cf14b2d5ace5941bb68ede7276922ea36ee457d76ad
ARG BASE_IMAGE=python:3.13-slim@sha256:70729b46c69b4f1e97c4822c1af3df53a1476cf5ddc6c087c0c10bc3a5678c2f

FROM ${DOCKER_CLI_IMAGE} AS docker-cli
FROM ${BASE_IMAGE}

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1 \
    DOCKER_CONFIG=/tmp/.docker

COPY requirements-dev.lock /tmp/requirements-dev.lock
RUN python -m pip install --no-cache-dir --require-hashes \
      -r /tmp/requirements-dev.lock

COPY --from=docker-cli /usr/local/bin/docker /usr/local/bin/docker
COPY --from=docker-cli /usr/local/libexec/docker/cli-plugins /usr/local/libexec/docker/cli-plugins

RUN useradd --uid 10001 --create-home app \
 && install -d -o app -g app /app \
 && { \
      python --version 2>&1; \
      python -m pip --version; \
      docker --version; \
    } > /opt/toolchain.lock

WORKDIR /app
COPY --chown=app:app services/draft/draft/ ./draft/
COPY --chown=app:app services/draft/tests/ ./tests/
COPY --chown=app:app fixtures/draft/ ./fixtures/draft/
COPY --chown=app:app scripts/ ./scripts/

USER app
ENTRYPOINT ["python", "-m", "draft.cli"]
CMD ["version"]
