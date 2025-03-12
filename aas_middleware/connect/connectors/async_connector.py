from typing import AsyncGenerator, Callable, Awaitable, Protocol

from typing import Optional, Protocol, Any, runtime_checkable

from aas_middleware.connect.connectors.connector import Connector

@runtime_checkable
class Receiver(Protocol):
    async def connect(self) -> None:
        """
        Raises:
            ConnectionError: If the connection to the server could not be established.
        """
        ...
    
    async def disconnect(self) -> None:
        """
        Raises:
            ConnectionError: If the connection to the server could not be established.
        """
        ...

    async def receive(self) -> AsyncGenerator[Any, None]:
        """
        Interfaces for a receiver to receive data in an asynchronous way. Instead of providing the last value (as the provide() method does), this method gives a generator that yields the data as it is received.

        Yields:
            Any: The data to be received.

        Raises:
            ConnectionError: If the receiving of the data failed.
        """
        ...

class AsyncConnector(Connector, Receiver): ...
