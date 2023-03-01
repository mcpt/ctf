FROM python:3.10.10-slim@sha256:f3be7f3778b538bdaa97a5dbb09c7427bdb3ac85e40aaa32eb4d9b3d66320e47

RUN adduser --system --home /app --gecos "mCTF" ctf && \
    groupadd ctf && \
    usermod -g ctf ctf && \
    apt-get update && \
    apt-get install -y build-essential && \
    apt-get install -y libsass-dev && \
    rm -rf /var/lib/apt/lists/*

WORKDIR /app2/media
WORKDIR /app2/static
WORKDIR /app
USER ctf
RUN python -m pip install --no-cache-dir poetry

COPY poetry.lock pyproject.toml /app/
RUN python -m poetry config virtualenvs.in-project true && \
    python -m poetry install --no-root
USER root
RUN apt-get purge -y build-essential && \
    rm -rf /var/lib/apt/lists/*
RUN rm -rf /var/cache/*
USER ctf

COPY . /app/
COPY ./mCTF/docker_config.py /app/mCTF/config.py

USER root
CMD /app/.venv/bin/gunicorn \
      --bind unix:/run/gunicorn.sock \
      --error-logfile - \
      --config /app/container/gunicorn.py \
      mCTF.wsgi:application
