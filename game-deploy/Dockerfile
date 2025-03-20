FROM python:3.12-bullseye

ENV POETRY_HOME=/root/.poetry
ENV PATH=$PATH:/root/.poetry/bin
ENV PYTHONPATH /usr/app/

WORKDIR /usr/app/

RUN curl -sSL https://install.python-poetry.org | python3 -
RUN poetry config virtualenvs.create false
COPY pyproject.toml poetry.lock ./
RUN poetry install --only main

COPY . ./
