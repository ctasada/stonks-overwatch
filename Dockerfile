# syntax=docker/dockerfile:1
FROM python:3
# set environment variables
ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1

# install dependencies
RUN pip install --upgrade pip
COPY ./requirements.txt .
RUN pip install -r requirements.txt

WORKDIR /app

COPY ./src /app
# FIXME: Secrets must be provided in a more secure way
COPY ./config /app/config