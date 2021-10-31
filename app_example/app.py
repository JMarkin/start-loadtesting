# -*- coding: utf-8 -*-
"""
Пример простого приложеняи использующее редис и постгрес
"""
import json
import os
import socket
import time

import aioredis
import asyncpg
from fastapi import FastAPI, Request, Response
from pydantic import BaseModel
from prometheus_client import (  # type: ignore
    CollectorRegistry, Counter, Summary, CONTENT_TYPE_LATEST, generate_latest,
)
from elasticapm.contrib.starlette import ElasticAPM, make_apm_client

app = FastAPI()

CREATE_TABLE = """
create table if not exists "user" (
    id serial primary key not null,
    first_name varchar(10) not null,
    last_name varchar(10) not null
)
"""


class User(BaseModel):
    first_name: str
    last_name: str


CONNECTIONS = {}


@app.on_event("startup")
async def startup():
    """
    Определяем коннекты
    """
    conn = await asyncpg.create_pool(dsn=os.getenv("DB_DSN"))

    await conn.execute(CREATE_TABLE)

    CONNECTIONS["db"] = conn
    CONNECTIONS["redis"] = aioredis.from_url(os.getenv("REDIS_DSN"))


@app.get("/user/{user_id}/")
async def get(user_id: int):
    """
    Получение юзера по id
    """
    redis = CONNECTIONS["redis"]
    if user := (await redis.get(user_id)):
        return json.loads(user)

    pool = CONNECTIONS["db"]

    async with pool.acquire() as conn:

        user = await conn.fetchrow("select * from \"user\" where id=$1",
                                   user_id)

    user = dict(user)

    await redis.set(user_id, json.dumps(user), ex=60)

    return user


@app.get("/user/")
async def list():
    """
    Получение юзера по id
    """
    pool = CONNECTIONS["db"]

    async with pool.acquire() as conn:

        users = await conn.fetch(
            "select * from \"user\" order by id desc, first_name limit 10 offset 4"
        )

    users = [dict(user) for user in users]

    return users


@app.post("/user/")
async def post(user: User):
    """
    Создание юзера
    """
    pool = CONNECTIONS["db"]

    async with pool.acquire() as conn:
        user_id = await conn.fetchval(
            "insert into \"user\"(first_name, last_name) values ($1, $2) returning id",
            user.first_name, user.last_name)
        user = await conn.fetchrow("select * from \"user\" where id=$1",
                                   user_id)

    user = dict(user)

    redis = CONNECTIONS["redis"]
    await redis.set(user_id, json.dumps(user), ex=60)
    return user


@app.patch("/user/{user_id}")
async def patch(user_id: int, user: User):
    """
    Обновление юзера
    """
    pool = CONNECTIONS["db"]

    async with pool.acquire() as conn:
        await conn.execute(
            "update \"user\" set first_name=$1, last_name=$2 where id=$3",
            user.first_name, user.last_name, user_id)
        user = await conn.fetchrow("select * from \"user\" where id=$1",
                                   user_id)

    user = dict(user)

    redis = CONNECTIONS["redis"]

    await redis.set(user_id, json.dumps(user), ex=60)
    return user


class Metrics:
    @property
    def job(self) -> str:
        return self._job

    @property
    def instance(self) -> str:
        return socket.gethostname()

    def __init__(self, /, job: str = 'app') -> None:
        self.registry = CollectorRegistry()

        self._job = job

        # Количество запущенных процессов
        self.up = Counter(
            "up",
            "Instance availability",
            ["job", "instance"],
            registry=self.registry,
        ).labels(job=job, instance=self.instance)
        self.up.inc(1)

        # Количество обработанных запросов
        self.http_requests = Counter(
            "http_requests",
            "Total processed requests",
            ["job", "instance", "endpoint"],
            registry=self.registry,
        )

        # Время обработки запросов
        self.http_requests_seconds = Summary(
            "http_requests_seconds",
            "Total processed requests time",
            ["job", "instance", "endpoint"],
            registry=self.registry,
        )


metrics = Metrics()


@app.middleware("http")
async def metrics_middleware(request: Request, call_next):
    # Замеряем время выполнения запроса
    ts = time.monotonic()
    response = await call_next(request)
    elapsed = time.monotonic() - ts

    # Метрики
    metrics.http_requests_seconds.labels(
        job=metrics.job, instance=metrics.instance,
        endpoint=request.url.path).observe(elapsed)
    metrics.http_requests.labels(job=metrics.job,
                                 instance=metrics.instance,
                                 endpoint=request.url.path).inc()
    # Возвращаем ответ
    return response


@app.get("/metrics")
async def get_prometheus_metrics():
    data = generate_latest(metrics.registry)
    return Response(status_code=200,
                    content=data,
                    media_type=CONTENT_TYPE_LATEST)


APM_URL = os.getenv("APM_URL", "")

if APM_URL:
    apm = make_apm_client({
        "SERVICE_NAME": "app",
        "SERVER_URL": APM_URL,
    })
    app.add_middleware(ElasticAPM, client=apm)
