import asyncio
import json
import os
import sys
import aiomqtt
from contextlib import suppress
from typing import Any, AsyncGenerator, Optional


class MqttClientConnector:
    def __init__(self, broker_ip: str, topic: str):
        self.broker_ip = broker_ip
        self.topic = topic
        self.client: aiomqtt.Client = aiomqtt.Client(
            self.broker_ip,
            keepalive=60,
            clean_start=False,
        )
        self.queue: asyncio.Queue[Any] = asyncio.Queue()
        self.value: Optional[Any] = None
        self._runner: Optional[asyncio.Task] = None

    async def connect(self):
        """Start the background task that maintains the connection & listens."""
        if sys.platform.lower() == "win32" or os.name.lower() == "nt":
            from asyncio import set_event_loop_policy, WindowsSelectorEventLoopPolicy
            set_event_loop_policy(WindowsSelectorEventLoopPolicy())
        if self._runner is None:
            self._runner = asyncio.create_task(self._run_forever())

    async def disconnect(self):
        """Cancel background task and cleanly close the MQTT session."""
        if self._runner:
            self._runner.cancel()
            with suppress(asyncio.CancelledError):
                await self._runner
            self._runner = None

    async def consume(self, body: Any) -> None:
        """Publish a message immediately (errors will bubble up)."""
        payload = json.dumps(body)
        await self.client.publish(self.topic, payload)

    async def provide(self) -> Any:
        """Return the last‐seen message (or None if none yet)."""
        return self.value

    async def receive(self) -> AsyncGenerator[Any, None]:
        """
        Async generator that yields each message as it arrives.
        Usage:
            async for msg in connector.receive():
                ...
        """
        while True:
            msg = await self.queue.get()
            yield msg

    async def _run_forever(self):
        """Internal: connect, subscribe, listen, reconnect-on-failure."""
        backoff = 1
        while True:
            try:
                await self.client.__aenter__()
                await self.client.subscribe(self.topic)
                async for message in self.client.messages:
                    self.value = json.loads(message.payload.decode())
                    await self.queue.put(self.value)
                backoff = 1

            except asyncio.CancelledError:
                # shutdown requested
                break

            except Exception as exc:
                with suppress(Exception):
                    await self.client.__aexit__(None, None, None)
                await asyncio.sleep(backoff)
                backoff = min(backoff * 2, 60)

        with suppress(Exception):
            await self.client.__aexit__(None, None, None)
