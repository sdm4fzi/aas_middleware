import os
import sys


if sys.platform.startswith("win") or os.name == "nt":
    # BEFORE you import or call asyncio.run()
    from asyncio import set_event_loop_policy, WindowsSelectorEventLoopPolicy

    set_event_loop_policy(WindowsSelectorEventLoopPolicy())

import asyncio
import json
from typing import Any, AsyncGenerator, Optional
import aiomqtt


class MqttClientConnector:
    def __init__(self, broker_ip: str, topic: str):
        self.mqtt_broker_ip = broker_ip
        self.topic = topic
        self.client: aiomqtt.Client = None
        self.value = None
        self.queue = asyncio.Queue()

    async def connect(self):
        self.mqtt_client = aiomqtt.Client(self.mqtt_broker_ip)
        await self.mqtt_client.__aenter__()
        loop = asyncio.get_event_loop()
        task = loop.create_task(self.listen_for_mqtt_messages())

    async def listen_for_mqtt_messages(self):
        await self.mqtt_client.subscribe(self.topic)
        async for message in self.mqtt_client.messages:
            self.value = json.loads(message.payload.decode())
            await self.queue.put(self.value)

    async def disconnect(self):
        await self.mqtt_client.__aexit__()

    async def consume(self, body: Optional[Any]) -> None:
        await self.mqtt_client.publish(self.topic, body)

    async def provide(self) -> Any:
        return self.value

    async def receive(self) -> AsyncGenerator[Any, None]:
        while True:
            new_value = await self.queue.get()
            yield new_value


if __name__ == "__main__":
    import asyncio
    import random

    async def main():
        mqtt_vda5050_feedback_provider = MqttClientConnector(
            broker_ip="172.22.192.101", topic="vda5050/feedback"
            # broker_ip="broker.emqx.io", topic="vda5050/feedback"
        )

        await mqtt_vda5050_feedback_provider.connect()
        print("Connected to MQTT broker")
        await mqtt_vda5050_feedback_provider.consume("Hello World")
        # print("Published message to topic")
        # async for message in mqtt_vda5050_feedback_provider.receive():
        #     print(f"Received message: {message}")
        #     await asyncio.sleep(1)

    asyncio.run(main())
