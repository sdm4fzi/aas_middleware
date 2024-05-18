from typing import Optional, Protocol


class Connector(Protocol):
    async def connect(self):
        ...

    async def disconnect(self):
        ...

    async def send(self, body: str) -> Optional[str]:
        ...

    async def receive(self) -> str:
        ...