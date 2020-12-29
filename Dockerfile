FROM python:3.9-alpine

LABEL maintainer="Kyunghan (Paul) Lee <contact@paullee.dev>"

RUN apk update
RUN apt-get update

RUN apk add --no-cache --virtual .build-deps \
    gcc \
    python3-dev \
    musl-dev \
    postgresql-dev \
    && python3 -m pip install --no-cache-dir psycopg2 \
    && apk del --no-cache .build-deps

WORKDIR /app

COPY requirements.txt /app/

RUN python3 -m pip install -r requirements.txt

COPY . /app/

EXPOSE 8000

CMD ["gunicorn", "pCTF.wsgi", "-b", "0.0.0.0:8000"]
