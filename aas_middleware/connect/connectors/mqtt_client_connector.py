import asyncio
import json
import os
import sys
from typing import Any, Optional
import aiomqtt

class MqttClientConnector:
    def __init__(self, broker_ip: str, topic: str):
        self.mqtt_broker_ip = broker_ip
        self.topic = topic
        self.client: aiomqtt.Client = None
        self.value = None

    async def connect(self):
        if sys.platform.lower() == "win32" or os.name.lower() == "nt":
            from asyncio import set_event_loop_policy, WindowsSelectorEventLoopPolicy
            set_event_loop_policy(WindowsSelectorEventLoopPolicy())
        self.mqtt_client = aiomqtt.Client(self.mqtt_broker_ip)
        await self.mqtt_client.__aenter__()
        loop = asyncio.get_event_loop()
        task = loop.create_task(self.listen_for_mqtt_messages())  

    async def listen_for_mqtt_messages(self):
        await self.mqtt_client.subscribe(self.topic)
        async for message in self.mqtt_client.messages:
            self.value = json.loads(message.payload.decode())
                
    async def disconnect(self):
        await self.mqtt_client.__aexit__()

    async def consume(self, body: Optional[Any
    ]) -> None:
        await self.mqtt_client.publish(self.topic, body)

    async def provide(self) -> Any:
        return self.value
