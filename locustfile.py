# -*- coding: utf-8 -*-

import time
from random import randint, random

from locust import SequentialTaskSet, task, FastHttpUser, constant


class MyTaskSet(SequentialTaskSet):
    wait_time = constant(1)

    @task
    def post(self):
        resp = self.client.post("/user/",
                                json={
                                    "first_name": str(random())[:9],
                                    "last_name": str(random())[:9]
                                },
                                name="create")
        data = resp.json()
        self.id = data["id"]

    @task(2)
    def get(self):
        self.client.get(f"/user/{self.id}/", name="get")

    @task
    def patch(self):
        self.client.patch(f"/user/{self.id}",
                          json={
                              "first_name": str(random())[:9],
                              "last_name": str(random())[:9]
                          },
                          name="update")

    @task(2)
    def list(self):
        self.client.get("/user/", name="list")


class Locust(FastHttpUser):
    tasks = [MyTaskSet]
