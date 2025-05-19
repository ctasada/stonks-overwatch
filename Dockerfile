# syntax=docker/dockerfile:1
FROM python:3-slim AS builder
# set environment variables
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

RUN apt-get update && \
    apt-get upgrade -y && \
    apt-get install sqlite3 nodejs npm -y && \
    apt-get autoremove && \
    apt-get clean -y

ENV POETRY_NO_INTERACTION=1 \
    POETRY_VIRTUALENVS_IN_PROJECT=1 \
    POETRY_VIRTUALENVS_CREATE=1 \
    POETRY_CACHE_DIR=/tmp/poetry_cache

RUN pip install poetry

# install Poetry dependencies
WORKDIR /app
COPY pyproject.toml ./
RUN poetry install --without dev --no-root && rm -rf "$POETRY_CACHE_DIR"

# install Node dependencies
WORKDIR /app/src
COPY src/package.json ./
RUN npm install

# The runtime image, used to just run the code provided its virtual environment
FROM python:3-slim AS runtime

# set environment variables
ENV PYTHONDONTWRITEBYTECODE 1 \
    PYTHONUNBUFFERED 1

RUN apt-get update && \
    apt-get upgrade -y && \
    apt-get install sqlite3 nodejs npm -y && \
    apt-get autoremove && \
    apt-get clean -y

WORKDIR /app

ENV VIRTUAL_ENV=/app/.venv \
    PATH="/app/.venv/bin:$PATH" \
    FORCE_COLOR="1"

COPY --from=builder ${VIRTUAL_ENV} ${VIRTUAL_ENV}
COPY --from=builder /app/src/node_modules /app/src/node_modules

COPY ./src /app/src
COPY ./scripts/init.sh /app/init.sh
# FIXME: Secrets must be provided in a more secure way
COPY ./config /app/config
