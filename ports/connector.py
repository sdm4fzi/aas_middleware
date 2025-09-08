"""
Unified Connector protocol for the middleware system.

This protocol defines the single interface that all connectors must implement,
combining the functionality of providers, consumers, and receivers.
"""

from typing import Protocol, AsyncIterator, Mapping, Any, TypeVar, Generic

T = TypeVar("T")

class Connector(Protocol, Generic[T]):
    """
    Unified protocol for all connectors in the middleware system.
    
    This protocol combines the functionality of:
    - Provider: provide() for pulling latest values
    - Consumer: consume() for pushing values  
    - Receiver: receive() for streaming values
    """
    
    async def provide(self) -> T:
        """
        Return the latest/current value (snapshot).
        
        This method should return the most recent value available from the connector.
        For connectors that don't maintain state, this may return None or raise
        an appropriate exception.
        
        Returns:
            T: The latest value from the connector
            
        Raises:
            ConnectionError: If the connection failed
            ValueError: If no value is available
        """
        ...

    async def consume(self, value: T, *, meta: Mapping[str, Any] | None = None) -> None:
        """
        Accept a value (push/post).
        
        This method should accept a value and process it according to the connector's
        implementation. The meta parameter can contain additional metadata about
        the value being consumed.
        
        Args:
            value: The value to consume
            meta: Optional metadata about the value
            
        Raises:
            ConnectionError: If the connection failed
            ValueError: If the value is invalid for this connector
        """
        ...

    async def receive(self) -> AsyncIterator[T]:
        """
        Stream values as they arrive (events/changes).
        
        This method should yield values as they become available from the connector.
        For connectors that don't support streaming, this may yield only the current
        value or raise an appropriate exception.
        
        Yields:
            T: Values as they arrive from the connector
            
        Raises:
            ConnectionError: If the connection failed
        """
        ...
