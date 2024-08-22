# syntax=docker/dockerfile:1
FROM python:3-slim as builder
# set environment variables
ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1

ENV POETRY_NO_INTERACTION=1 \
    POETRY_VIRTUALENVS_IN_PROJECT=1 \
    POETRY_VIRTUALENVS_CREATE=1 \
    POETRY_CACHE_DIR=/tmp/poetry_cache

RUN apt-get update && \
    apt-get upgrade -y && \
    apt-get install sqlite3 && \
    apt-get autoremove && \
    apt-get clean -y
RUN pip install poetry

WORKDIR /app

# install dependencies
COPY pyproject.toml poetry.lock ./
RUN poetry install --no-root && rm -rf $POETRY_CACHE_DIR

# The runtime image, used to just run the code provided its virtual environment
FROM python:3-slim as runtime

WORKDIR /app

ENV VIRTUAL_ENV=/app/.venv \
    PATH="/app/.venv/bin:$PATH"

COPY --from=builder ${VIRTUAL_ENV} ${VIRTUAL_ENV}

COPY ./src /app
# FIXME: Secrets must be provided in a more secure way
COPY ./config /config
# FIXME: Database should be created if doesn't exist
CMD ["poetry run src/manage.py runserver"]