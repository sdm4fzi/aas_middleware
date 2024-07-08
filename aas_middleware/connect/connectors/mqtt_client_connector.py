import asyncio
from typing import Any, Optional
import aiomqtt


# TODO: use fastapi support form aiomqtt: https://sbtinstruments.github.io/aiomqtt/alongside-fastapi-and-co.html

class MqttClientConnector:
    def __init__(self, broker_ip: str, topic: str):
        self.mqtt_broker_ip = broker_ip
        self.topic = topic
        self.client: aiomqtt.Client = None
        self.value = None

    async def connect(self):
        print("connect client")
        async with aiomqtt.Client(self.mqtt_broker_ip) as mqtt_client:
            print("connected")
            self.mqtt_client = mqtt_client
            # async with asyncio.TaskGroup() as tg:
            #     tg.create_task(self.listen_for_mqtt_messages())
            await self.mqtt_client.subscribe(self.topic)
            async for message in self.mqtt_client.messages:
                print("message received with payload:", message.payload)
            self.value = message.payload
            # loop = asyncio.get_event_loop()
            # task = loop.create_task(self.listen_for_mqtt_messages(mqtt_client))  


    async def listen_for_mqtt_messages(self, client: aiomqtt.Client):
        print("listening for messages")
        await self.mqtt_client.subscribe(self.topic)
        async for message in self.mqtt_client.messages:
            print("message received with payload:", message.payload)
            self.value = message.payload
        print("done listening")
                
    async def disconnect(self):
        pass

    async def consume(self, body: Optional[Any
    ]) -> None:
        await self.mqtt_client.publish(self.topic, body)

    async def provide(self) -> Any:
        return self.value
