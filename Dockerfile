FROM python:3.11.5-slim@sha256:3542a2fcc89c24f7f4ed6fa6b1892175452cf8b612cc86168bd849b48b092a95

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
EXPOSE 28730
CMD /app/.venv/bin/gunicorn \
      --bind :28730 \
      --error-logfile - \
      --config /app/container/gunicorn.py \
      mCTF.wsgi:application
