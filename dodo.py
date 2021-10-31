# -*- coding: utf-8 -*-
import glob
import json
import os

PROJECT = os.getenv("PROJECT", "load")

COMPOSE_EXEC = f"docker-compose -p {PROJECT}"

APP_VAL = int(os.getenv("APP_VAL", "1"))

UPSTREAM_TEMPLATE = """
upstream app {{
  least_conn;
  
  {servers}
}}
"""


def create_upstream(count):
    servers = "\n".join(
        [f"server load-app-{i}:8000;" for i in range(1, count + 1)])
    with open("./nginx/upstream.conf", 'w') as f:
        f.write(UPSTREAM_TEMPLATE.format(servers=servers))


PROMETHEUS_TARGET_APP = {"labels": {"job": "app"}, "targets": []}


def create_appjson(count):

    PROMETHEUS_TARGET_APP["targets"] = [
        f"load-app-{i}:8000" for i in range(1, count + 1)
    ]
    with open("./prometheus/app.json", 'w') as f:
        f.write(json.dumps([PROMETHEUS_TARGET_APP]))


def task_build():
    DOCKERFILES = glob.glob('**/Dockerfile', recursive=True) + \
        glob.glob("**/*.dockerfile", recursive=True) + \
        glob.glob("**/*.sh", recursive=True)

    return {
        "actions": [f"{COMPOSE_EXEC} -f ./composes/app-compose.yml build"],
        "file_dep":
        DOCKERFILES + ["./composes/app-compose.yml", "./app_example/app.py"],
        "verbosity":
        2
    }


def task_up():
    yield {
        "name":
        "update upstreams",
        "actions": [(create_upstream, [], {
            "count": APP_VAL,
        }), (create_appjson, [], {
            "count": APP_VAL,
        })],
    }
    yield {
        "name":
        "up",
        "task_dep": ["build"],
        "actions": [
            f"{COMPOSE_EXEC} -f ./composes/app-compose.yml up -d --scale app={APP_VAL}",
        ],
        "file_dep": ["./composes/app-compose.yml", "./app_example/app.py"],
        "verbosity":
        2,
        "uptodate": [False]
    }


def task_monitoring():

    return {
        "actions": [
            f"{COMPOSE_EXEC} -f ./composes/monitoring-compose.yml -f ./composes/apm-compose.yml up -d"
        ],
        "file_dep": [
            "./composes/monitoring-compose.yml", "./prometheus/prometheus.yml",
            "./composes/apm-compose.yml"
        ],
        "verbosity":
        2,
    }
