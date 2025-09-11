import os
import sys


if sys.platform.startswith("win") or os.name == "nt":
    from asyncio import set_event_loop_policy, WindowsSelectorEventLoopPolicy
    set_event_loop_policy(WindowsSelectorEventLoopPolicy())

import asyncio
import json
from typing import Any, AsyncGenerator, Optional
import aiomqtt


class MqttClientConnector:
    def __init__(self, broker_ip: str, topic: str, port: int = 1883):
        self.mqtt_broker_ip = broker_ip
        self.mqtt_broker_port = port
        self.topic = topic
        self.client: aiomqtt.Client = None
        self.value = None
        self.queue = asyncio.Queue()
        self._listener = None

    async def _connect_client(self, max_retry_count: int = 5):
        retry_count = 0
        while retry_count < max_retry_count:
            try:
                retry_count += 1
                self.client = aiomqtt.Client(self.mqtt_broker_ip, port=self.mqtt_broker_port)
                await self.client.__aenter__()
                return
            except Exception as e:
                await asyncio.sleep(1)
        raise ConnectionError(
            f"Failed to connect to MQTT broker after {max_retry_count} attempts"
        )

    async def connect(self):
        await self._connect_client()
        loop = asyncio.get_event_loop()
        self._listener = loop.create_task(self.listen_for_mqtt_messages())

    async def listen_for_mqtt_messages(self):
        while True:
            try:
                await self.client.subscribe(self.topic)
                async for message in self.client.messages:
                    self.value = json.loads(message.payload.decode())
                    await self.queue.put(self.value)
            except Exception as e:
                await self._connect_client()

    async def disconnect(self):
        if self.client is None:
            return
        await self.client.__aexit__(exc_type=None, exc=None, tb=None)
        await self._listener.cancel()
        self._listener = None

    async def consume(self, body: Optional[Any]) -> None:
        try:
            await self.client.publish(self.topic, body)
        except Exception as e:
            await self._connect_client()
            await self.client.publish(self.topic, body)

    async def provide(self) -> Any:
        return self.value

    async def receive(self) -> AsyncGenerator[Any, None]:
        while True:
            new_value = await self.queue.get()
            yield new_value


async def main():
    broker_ip = "172.22.192.101"
    topic = "vda5050/feedback"
    port = 50000
    # port = 1883
    import time
    client = MqttClientConnector(broker_ip, topic, port)
    await client.connect()

    async def producer():
        msg_id = 0
        while True:
            # stamp with monotonic time for best precision
            ts = time.monotonic()
            payload = json.dumps({"id": msg_id, "ts": ts})
            await client.consume(payload)
            msg_id += 1
            await asyncio.sleep(0.001)  # adjust send rate as needed

    async def consumer():
        last_time = time.monotonic()
        async for data in client.receive():
            now = time.monotonic()
            latency_ms = (now - data["ts"]) * 1_000
            print(f"[Msg {data['id']}] round-trip latency: {latency_ms:.2f} ms time since last msg: {now -last_time:.2f} ms")
            last_time = now
    try:
        await asyncio.gather(producer(), consumer())
    finally:
        await client.disconnect()


if __name__ == "__main__":
    asyncio.run(main())
