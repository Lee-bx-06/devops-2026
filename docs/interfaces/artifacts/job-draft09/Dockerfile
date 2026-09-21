FROM ubuntu:24.04@sha256:9f1d0a0f26f37672b7f6f0f72b140c9f8e0d17df8f0c6197aa9b3b3d3a81a0c1

RUN apt-get update \
    && DEBIAN_FRONTEND=noninteractive apt-get install -y --no-install-recommends \
       gcc-13 \
       make \
       libssl-dev \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /workspace/project
