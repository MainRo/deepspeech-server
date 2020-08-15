FROM python:3.8-slim-buster

LABEL authors="Mohamed Laradji <mlaradji@protonmail.ch>"
LABEL maintainer="Mohamed Laradji <mlaradji@protonmail.ch>"

# Get pre-trained model.
RUN mkdir -p /app/data/working/
ADD https://github.com/mozilla/DeepSpeech/releases/download/v0.7.1/deepspeech-0.7.1-models.pbmm /app/data/working/
ADD https://github.com/mozilla/DeepSpeech/releases/download/v0.7.1/deepspeech-0.7.1-models.scorer /app/data/working/

# System dependencies
# ?: Not sure if both libstdc++-*-dev are required
RUN apt-get update && apt-get install -y --no-install-recommends \
  gcc \
  python3-dev \
  pipenv \
  supervisor

# Project dependencies and codebase
COPY . /app/
WORKDIR /app

# Install requirements. Since requirements are not system, use `pipenv run` inside the WORKDIR.
RUN pipenv install --deploy --ignore-pipfile

# Run service.
EXPOSE 8080
CMD ["/usr/bin/supervisord", "-c", "/app/docker/supervisord.conf"]

# Add a healthcheck.
HEALTHCHECK --interval=5m --timeout=3s CMD curl --data-binary=@/app/docker/pronunciation_en_meadows.mp3 -f http://localhost:8080/stt || exit 1