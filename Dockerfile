FROM python:3.11.5-slim@sha256:3542a2fcc89c24f7f4ed6fa6b1892175452cf8b612cc86168bd849b48b092a95

RUN adduser --system --home /app --gecos "mCTF" ctf && \
    groupadd ctf && \
    usermod -g ctf ctf && \
    apt-get update && \
    apt-get install -y build-essential python3-dev libpq-dev sassc libsass-dev libffi-dev && \
    pg_config --version && \
    rm -rf /var/lib/apt/lists/*

WORKDIR /app2/media
WORKDIR /app2/static
WORKDIR /app
USER ctf
RUN python -m pip install --no-cache-dir --no-warn-script-location poetry

COPY poetry.lock pyproject.toml /app/
RUN python -m poetry config virtualenvs.in-project true && \
    python -m poetry install --no-root
RUN /app/.venv/bin/pip install psycopg2
USER root
RUN apt-get purge -y build-essential && \
    rm -rf /var/lib/apt/lists/* && \
    rm -rf /var/cache/*
USER ctf

COPY . /app/
COPY ./mCTF/docker_config.py /app/mCTF/config.py
USER root
RUN set -eux; cd /app/public/scss; mkdir out; for f in *.scss; \
    do \
      sassc --style compressed -- "$f" "out/${f%.scss}.css"; \
    done; \
    mv out/* .; \
    chmod a+r /app/public/scss/*.css

STOPSIGNAL SIGINT
# Django listens to SIGINT but not SIGTERM
RUN apt-get purge -y sassc && \
    rm -rf /var/lib/apt/lists/* && \
    rm -rf /var/cache/*
EXPOSE 28730
CMD /app/.venv/bin/gunicorn \
      --bind :28730 \
      --error-logfile - \
      --timeout 120 \
      --config /app/container/gunicorn.py \
      mCTF.wsgi:application
