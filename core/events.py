"""
Event bus system for middleware instrumentation and observability.

This module provides an event bus that allows components to publish and subscribe
to events for monitoring, debugging, and integration purposes.
"""

from typing import Any, Callable, Dict, List, Optional, Set
from dataclasses import dataclass
from datetime import datetime
import asyncio
import logging

logger = logging.getLogger(__name__)

@dataclass
class Event:
    """Represents an event in the system."""
    name: str
    timestamp: datetime
    data: Dict[str, Any]
    source: str
    correlation_id: Optional[str] = None


class EventBus:
    """
    Event bus for publishing and subscribing to system events.
    
    This class provides a simple pub/sub mechanism for system-wide events,
    enabling instrumentation, monitoring, and integration capabilities.
    """
    
    def __init__(self):
        self._subscribers: Dict[str, Set[Callable[[Event], None]]] = {}
        self._async_subscribers: Dict[str, Set[Callable[[Event], Any]]] = {}
        self._event_history: List[Event] = []
        self._max_history = 1000
        
    def subscribe(
        self, 
        event_name: str, 
        callback: Callable[[Event], None]
    ) -> None:
        """
        Subscribe to events with the given name.
        
        Args:
            event_name: Name of the event to subscribe to
            callback: Function to call when the event occurs
        """
        if event_name not in self._subscribers:
            self._subscribers[event_name] = set()
        self._subscribers[event_name].add(callback)
        
    def subscribe_async(
        self, 
        event_name: str, 
        callback: Callable[[Event], Any]
    ) -> None:
        """
        Subscribe to events with an async callback.
        
        Args:
            event_name: Name of the event to subscribe to
            callback: Async function to call when the event occurs
        """
        if event_name not in self._async_subscribers:
            self._async_subscribers[event_name] = set()
        self._async_subscribers[event_name].add(callback)
        
    def unsubscribe(
        self, 
        event_name: str, 
        callback: Callable[[Event], None]
    ) -> None:
        """
        Unsubscribe from events with the given name.
        
        Args:
            event_name: Name of the event to unsubscribe from
            callback: Function to remove from subscribers
        """
        if event_name in self._subscribers:
            self._subscribers[event_name].discard(callback)
            
    def unsubscribe_async(
        self, 
        event_name: str, 
        callback: Callable[[Event], Any]
    ) -> None:
        """
        Unsubscribe from events with an async callback.
        
        Args:
            event_name: Name of the event to unsubscribe from
            callback: Async function to remove from subscribers
        """
        if event_name in self._async_subscribers:
            self._async_subscribers[event_name].discard(callback)
            
    def publish(
        self, 
        event_name: str, 
        data: Dict[str, Any], 
        source: str,
        correlation_id: Optional[str] = None
    ) -> None:
        """
        Publish an event to all subscribers.
        
        Args:
            event_name: Name of the event
            data: Event data
            source: Source of the event
            correlation_id: Optional correlation ID for tracing
        """
        event = Event(
            name=event_name,
            timestamp=datetime.utcnow(),
            data=data,
            source=source,
            correlation_id=correlation_id
        )
        
        # Store in history
        self._event_history.append(event)
        if len(self._event_history) > self._max_history:
            self._event_history.pop(0)
            
        # Notify sync subscribers
        if event_name in self._subscribers:
            for callback in self._subscribers[event_name]:
                try:
                    callback(event)
                except Exception as e:
                    logger.error(f"Error in event subscriber: {e}")
                    
        # Schedule async subscribers
        if event_name in self._async_subscribers:
            for callback in self._async_subscribers[event_name]:
                asyncio.create_task(self._call_async_callback(callback, event))
                
    async def _call_async_callback(
        self, 
        callback: Callable[[Event], Any], 
        event: Event
    ) -> None:
        """Call an async callback and handle any errors."""
        try:
            await callback(event)
        except Exception as e:
            logger.error(f"Error in async event subscriber: {e}")
            
    def get_event_history(
        self, 
        event_name: Optional[str] = None,
        limit: Optional[int] = None
    ) -> List[Event]:
        """
        Get event history, optionally filtered by event name.
        
        Args:
            event_name: Optional event name to filter by
            limit: Optional limit on number of events to return
            
        Returns:
            List of events matching the criteria
        """
        events = self._event_history
        if event_name:
            events = [e for e in events if e.name == event_name]
            
        if limit:
            events = events[-limit:]
            
        return events.copy()
        
    def clear_history(self) -> None:
        """Clear the event history."""
        self._event_history.clear()
