FROM python:3.8-slim-buster

LABEL authors="Mohamed Laradji <mlaradji@protonmail.ch>"
LABEL maintainer="Mohamed Laradji <mlaradji@protonmail.ch>"

# System dependencies
# ?: Not sure if both libstdc++-*-dev are required
RUN apt-get update && apt-get install -y --no-install-recommends \
  vim \
  gcc \
  libpq-dev \
  python3-dev \
  libstdc++-7-dev \
  libstdc++-8-dev \
  pipenv \
  supervisor

# Project dependencies and codebase
COPY . /app/
WORKDIR /app

# Install requirements. Since requirements are not system, use `pipenv run` inside the WORKDIR.
RUN pipenv install --deploy --ignore-pipfile

# Run service.
ADD supervisord.conf /etc/supervisor/conf.d/supervisord.conf
CMD ["/usr/bin/supervisord", "-c", "/etc/supervisor/conf.d/supervisord.conf"]