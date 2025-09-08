"""
Memory connector for in-memory persistence.

This connector provides in-memory storage capabilities and serves
as the default persistence backend for the middleware system.
"""

from typing import AsyncIterator, Mapping, Any, Dict, Optional, TypeVar, Generic
from ...ports.connector import Connector
from ...ports.lifecycle import Connectable
from ...domain.data_model import DataModel
import asyncio
import logging

logger = logging.getLogger(__name__)

T = TypeVar("T", bound=DataModel)

class MemoryConnector(Connector[T], Connectable, Generic[T]):
    """
    In-memory connector for data persistence.
    
    This connector stores data in memory and provides the basic
    persistence capabilities required by the middleware system.
    """
    
    def __init__(self, model_name: str, type_name: str, field_name: Optional[str] = None):
        """
        Initialize the memory connector.
        
        Args:
            model_name: Name of the data model
            type_name: Name of the model type
            field_name: Optional field name for field-level persistence
        """
        self.model_name = model_name
        self.type_name = type_name
        self.field_name = field_name
        self._storage: Dict[str, Any] = {}
        self._connected = False
        self._subscribers: set = set()
        
    async def connect(self) -> None:
        """Establish connection (no-op for memory connector)."""
        self._connected = True
        logger.debug(f"Memory connector {self._get_id()} connected")
        
    async def disconnect(self) -> None:
        """Close connection (no-op for memory connector)."""
        self._connected = False
        logger.debug(f"Memory connector {self._get_id()} disconnected")
        
    async def provide(self) -> T:
        """
        Provide the latest value from storage.
        
        Returns:
            The latest value or None if no value exists
            
        Raises:
            ConnectionError: If not connected
        """
        if not self._connected:
            raise ConnectionError("Memory connector not connected")
            
        if self.field_name:
            # Return field value if specified
            if not self._storage:
                return None
            return self._storage.get(self.field_name)
        else:
            # Return the entire stored value
            if not self._storage:
                return None
            return list(self._storage.values())[0] if self._storage else None
            
    async def consume(self, value: T, *, meta: Mapping[str, Any] | None = None) -> None:
        """
        Store a value in memory.
        
        Args:
            value: The value to store
            meta: Optional metadata about the value
            
        Raises:
            ConnectionError: If not connected
        """
        if not self._connected:
            raise ConnectionError("Memory connector not connected")
            
        if self.field_name:
            # Store field value
            self._storage[self.field_name] = value
        else:
            # Store entire value with generated key
            key = f"{self.type_name}_{len(self._storage)}"
            self._storage[key] = value
            
        # Notify subscribers
        await self._notify_subscribers(value)
        logger.debug(f"Stored value in {self._get_id()}")
        
    async def receive(self) -> AsyncIterator[T]:
        """
        Stream values as they are stored.
        
        Yields:
            Values as they are consumed
            
        Raises:
            ConnectionError: If not connected
        """
        if not self._connected:
            raise ConnectionError("Memory connector not connected")
            
        # First yield any existing values
        for value in self._storage.values():
            yield value
            
        # Then wait for new values
        while self._connected:
            # This is a simplified implementation
            # In a real system, you might use asyncio.Event or similar
            await asyncio.sleep(0.1)
            
    def _get_id(self) -> str:
        """Get the connector identifier."""
        if self.field_name:
            return f"persist:{self.model_name}/{self.type_name}.{self.field_name}"
        else:
            return f"persist:{self.model_name}/{self.type_name}"
            
    async def _notify_subscribers(self, value: T) -> None:
        """Notify subscribers of new values."""
        for subscriber in self._subscribers:
            try:
                if asyncio.iscoroutinefunction(subscriber):
                    await subscriber(value)
                else:
                    subscriber(value)
            except Exception as e:
                logger.error(f"Error notifying subscriber: {e}")
                
    def subscribe(self, callback) -> None:
        """
        Subscribe to value changes.
        
        Args:
            callback: Function to call when values change
        """
        self._subscribers.add(callback)
        
    def unsubscribe(self, callback) -> None:
        """
        Unsubscribe from value changes.
        
        Args:
            callback: Function to remove from subscribers
        """
        self._subscribers.discard(callback)
        
    def clear(self) -> None:
        """Clear all stored values."""
        self._storage.clear()
        logger.debug(f"Cleared storage in {self._get_id()}")
        
    def get_storage_info(self) -> Dict[str, Any]:
        """
        Get information about the storage.
        
        Returns:
            Dictionary containing storage metadata
        """
        return {
            "connector_id": self._get_id(),
            "model_name": self.model_name,
            "type_name": self.type_name,
            "field_name": self.field_name,
            "connected": self._connected,
            "storage_size": len(self._storage),
            "subscriber_count": len(self._subscribers)
        }
