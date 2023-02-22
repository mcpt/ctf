FROM python:3.10.10-slim@sha256:f3be7f3778b538bdaa97a5dbb09c7427bdb3ac85e40aaa32eb4d9b3d66320e47

RUN adduser --system --home /app --gecos "mCTF" ctf && \
    groupadd ctf && \
    usermod -g ctf ctf && \
    apt-get update && \
    apt-get install -y uwsgi uwsgi-plugin-python3 && \
    rm -rf /var/lib/apt/lists/*

WORKDIR /app
USER ctf
RUN python -m pip install --no-cache-dir poetry

COPY poetry.lock pyproject.toml /app/
RUN python -m poetry config virtualenvs.in-project true && \
    python -m poetry install --no-root

USER root
RUN rm -rf /var/cache/*
USER ctf

COPY . /app/

EXPOSE 28730
COPY uwsgi.ini /app/
USER root
CMD ["uwsgi", "--ini", "/app/uwsgi.ini"]
