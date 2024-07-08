from __future__ import annotations
import os
import sys

from fastapi import middleware
import uvicorn

from aas_middleware.connect.connectors.mqtt_client_connector import MqttClientConnector

from aas_middleware.middleware.middleware import Middleware

if sys.platform.lower() == "win32" or os.name.lower() == "nt":
    from asyncio import set_event_loop_policy, WindowsSelectorEventLoopPolicy
    set_event_loop_policy(WindowsSelectorEventLoopPolicy())


mqtt_connector = MqttClientConnector("172.22.192.101", "mes/health")

mware = Middleware()

mware.add_connector("mqtt_connector", mqtt_connector, model_type=str)

mware.generate_connector_endpoints()


if __name__ == "__main__":
    uvicorn.run("middleware_mqtt_test:mware.app", reload=True)
    # uvicorn.run(mware.app)
