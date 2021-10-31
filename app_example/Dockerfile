FROM python:3.9-slim


RUN apt-get update && apt-get install -y iputils-ping &&\
      pip install -U fastapi asyncpg uvicorn aioredis elastic-apm uvloop prometheus-client

COPY ./app.py /

WORKDIR /

EXPOSE 8000

CMD uvicorn app:app --host 0.0.0.0
