FROM python:3.12-slim

RUN apt-get update && apt-get install -y bash

WORKDIR /project

COPY ["pyproject.toml", "poetry.lock", "alembic.ini", "README.md", "/project/"]
RUN pip install poetry
RUN poetry config virtualenvs.create false && \
    poetry install --no-interaction --no-root

COPY ["src", "/project/src"]
