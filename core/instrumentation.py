"""
Instrumentation system for automatic event emission.

This module provides wrapper classes that automatically emit events
when connector methods are called, enabling observability without
requiring connector authors to manually emit events.
"""

from typing import AsyncIterator, Mapping, Any, TypeVar, Generic
from .ports.connector import Connector
from .events import EventBus
import logging

logger = logging.getLogger(__name__)

T = TypeVar("T")

class InstrumentedConnector(Connector[T], Generic[T]):
    """
    Wrapper that automatically emits events for connector operations.
    
    This class wraps any connector and automatically emits events
    for provide, consume, and receive operations, enabling
    observability without requiring connector authors to manually
    emit events.
    """
    
    def __init__(self, inner: Connector[T], connector_id: str, event_bus: EventBus):
        """
        Initialize the instrumented connector.
        
        Args:
            inner: The underlying connector to wrap
            connector_id: Unique identifier for the connector
            event_bus: Event bus for emitting events
        """
        self._inner = inner
        self._connector_id = connector_id
        self._event_bus = event_bus
        
    async def provide(self) -> T:
        """
        Provide the latest value with automatic event emission.
        
        Returns:
            The latest value from the connector
            
        Raises:
            Any exception from the underlying connector
        """
        try:
            # Emit provide start event
            self._event_bus.publish(
                "connector.provide.start",
                data={"connector_id": self._connector_id},
                source=self._connector_id
            )
            
            # Call the underlying connector
            value = await self._inner.provide()
            
            # Emit provide success event
            self._event_bus.publish(
                "connector.provide.success",
                data={
                    "connector_id": self._connector_id,
                    "value_type": type(value).__name__
                },
                source=self._connector_id
            )
            
            return value
            
        except Exception as e:
            # Emit provide error event
            self._event_bus.publish(
                "connector.provide.error",
                data={
                    "connector_id": self._connector_id,
                    "error": str(e),
                    "error_type": type(e).__name__
                },
                source=self._connector_id
            )
            raise
            
    async def consume(self, value: T, *, meta: Mapping[str, Any] | None = None) -> None:
        """
        Consume a value with automatic event emission.
        
        Args:
            value: The value to consume
            meta: Optional metadata about the value
            
        Raises:
            Any exception from the underlying connector
        """
        try:
            # Emit consume start event
            self._event_bus.publish(
                "connector.consume.start",
                data={
                    "connector_id": self._connector_id,
                    "value_type": type(value).__name__,
                    "meta": meta or {}
                },
                source=self._connector_id
            )
            
            # Call the underlying connector
            await self._inner.consume(value, meta=meta)
            
            # Emit consume success event
            self._event_bus.publish(
                "connector.consume.success",
                data={
                    "connector_id": self._connector_id,
                    "value_type": type(value).__name__
                },
                source=self._connector_id
            )
            
        except Exception as e:
            # Emit consume error event
            self._event_bus.publish(
                "connector.consume.error",
                data={
                    "connector_id": self._connector_id,
                    "error": str(e),
                    "error_type": type(e).__name__
                },
                source=self._connector_id
            )
            raise
            
    async def receive(self) -> AsyncIterator[T]:
        """
        Receive values with automatic event emission.
        
        Yields:
            Values as they arrive from the connector
            
        Raises:
            Any exception from the underlying connector
        """
        # Emit receive start event
        self._event_bus.publish(
            "connector.receive.start",
            data={"connector_id": self._connector_id},
            source=self._connector_id
        )
        
        try:
            async for item in self._inner.receive():
                # Emit receive item event
                self._event_bus.publish(
                    "connector.receive.item",
                    data={
                        "connector_id": self._connector_id,
                        "item_type": type(item).__name__
                    },
                    source=self._connector_id
                )
                yield item
                
            # Emit receive complete event
            self._event_bus.publish(
                "connector.receive.complete",
                data={"connector_id": self._connector_id},
                source=self._connector_id
            )
            
        except Exception as e:
            # Emit receive error event
            self._event_bus.publish(
                "connector.receive.error",
                data={
                    "connector_id": self._connector_id,
                    "error": str(e),
                    "error_type": type(e).__name__
                },
                source=self._connector_id
            )
            raise


def instrument_connector(
    connector: Connector[T], 
    connector_id: str, 
    event_bus: EventBus
) -> InstrumentedConnector[T]:
    """
    Create an instrumented connector wrapper.
    
    Args:
        connector: The connector to instrument
        connector_id: Unique identifier for the connector
        event_bus: Event bus for emitting events
        
    Returns:
        Instrumented connector wrapper
    """
    return InstrumentedConnector(connector, connector_id, event_bus)
