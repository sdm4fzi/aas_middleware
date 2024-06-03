from typing import Optional, Protocol, Any

# TODO: think about making the connector a Generic for the types...

class Provider(Protocol):
    async def connect(self):
        ...

    async def disconnect(self):
        ...

    async def provide(self) -> Any:
        ...


class Consumer(Protocol):
    async def connect(self):
        ...

    async def disconnect(self):
        ...

    async def consume(self, body: Any) -> None:
        ...



class Connector(Provider, Consumer):
    ...