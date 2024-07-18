from __future__ import annotations
import asyncio
import os
import sys

from pydantic import BaseModel
import uvicorn


if sys.platform.lower() == "win32" or os.name.lower() == "nt":
    from asyncio import set_event_loop_policy, WindowsSelectorEventLoopPolicy
    set_event_loop_policy(WindowsSelectorEventLoopPolicy())

import aas_middleware


mqtt_connector = aas_middleware.connectors.MqttClientConnector("172.22.192.101", "mes/health")

mware = aas_middleware.Middleware()

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
