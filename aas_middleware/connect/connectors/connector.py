from typing import Optional, Protocol, Any, runtime_checkable

@runtime_checkable
class Provider(Protocol):
    async def connect(self):
        """
        Raises:
            ConnectionError: If the connection to the server could not be established.
        """
        ...

    async def disconnect(self):
        """
        Raises:
            ConnectionError: If the connection to the server could not be established.
        """
        ...

    async def provide(self) -> Any:
        """
        Interfaces for a provider to provide data.

        Returns:
            Any: The data to be provided.

        Raises:
            ConnectionError: If the providing of the data failed.
        """
        ...


@runtime_checkable
class Consumer(Protocol):
    async def connect(self):
        """
        Raises:
            ConnectionError: If the connection to the server could not be established.
        """
        ...

    async def disconnect(self):
        """
        Raises:
            ConnectionError: If the connection to the server could not be established.
        """
        ...

    async def consume(self, body: Any) -> None:
        """
        Interfaces for a consumer to consume data and send in with the connection to the consumer.

        Args:
            body (Any): The data to be consumed.

        Raises:
            ConnectionError: If the consuming of the data failed.
        """
        ...


class Connector(Provider, Consumer): ...
