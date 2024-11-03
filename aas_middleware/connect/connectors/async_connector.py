from typing import Callable, Awaitable, Protocol

from typing import Optional, Protocol, Any, runtime_checkable

@runtime_checkable
class Subsciber(Protocol):
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

    async def subscribe(self, topic: str) -> None:
        """
        Interfaces for a subscriber to subscribe to a topic and receive messages.

        Args:
            topic (str): The topic to subscribe to.

        Raises:
            ConnectionError: If the subscribing to the topic failed.
        """
        ...

    async def on_message(self, body: Any) -> None:
        """
        Interface for a subscriber to be executed upon arrival of a message from the subscriber.

        Args:
            body (Any): The body of the message received.
        """
        ...


@runtime_checkable
class Publisher(Protocol):
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

    async def publish(self, topic: str, body: Any) -> None:
        """
        Interfaces for a publisher to publish messages to a topic.

        Args:
            topic (str): The topic to publish the message to.
            body (Any): The body of the message to be published.

        Raises:
            ConnectionError: If the publishing of the message failed.
        """
        ...


class AsyncConnector(Subsciber, Publisher): ...
