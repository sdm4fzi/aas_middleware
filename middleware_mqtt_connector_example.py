from __future__ import annotations
import asyncio
import os
import stat
import sys

from fastapi import middleware
from pydantic import BaseModel
import uvicorn

import aas_middleware.connect
from aas_middleware.connect.connectors.mqtt_client_connector import MqttClientConnector

import aas_middleware.connect.workflows
from aas_middleware.middleware.middleware import Middleware

if sys.platform.lower() == "win32" or os.name.lower() == "nt":
    from asyncio import set_event_loop_policy, WindowsSelectorEventLoopPolicy
    set_event_loop_policy(WindowsSelectorEventLoopPolicy())

import aas_middleware


mqtt_connector = MqttClientConnector("172.22.192.101", "mes/health")

mware = Middleware()

class MesHealthMessage(BaseModel):
    status: str
    sentAt: str

# mware.add_connector("mqtt_connector", mqtt_connector, model_type=MesHealthMessage)

# mware.generate_connector_endpoints()


async def run_connector():
    await mqtt_connector.connect()

    for _ in range(50):
        mes_health = await mqtt_connector.provide()
        print(mes_health)
        await asyncio.sleep(1)


if __name__ == "__main__":
    # uvicorn.run("middleware_mqtt_test:mware.app", reload=True)
    # # uvicorn.run(mware.app)

    asyncio.run(run_connector())
