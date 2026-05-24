# Minimal Python sandbox for untrusted candidate code execution.
FROM python:3.12-alpine

RUN adduser -D -u 10001 sandbox \
    && pip install --no-cache-dir --disable-pip-version-check pip

USER sandbox
WORKDIR /home/sandbox

# Image tag used by DOCKER_EXECUTOR_IMAGE in settings
# Build: docker build -t dtae/python-sandbox:3.12 docker/sandbox
