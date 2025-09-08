"""
Service registry interface for service discovery.

This protocol defines the interface for service registries that can be used
to discover and register services in the middleware system.
"""

from typing import Protocol, Dict, Any, List, Optional
from abc import ABC, abstractmethod

class ServiceRegistry(Protocol):
    """
    Protocol for service registries that support service discovery.
    
    This protocol defines the interface for registering and discovering
    services in the middleware system.
    """
    
    async def register_service(
        self, 
        service_id: str, 
        service_info: Dict[str, Any]
    ) -> None:
        """
        Register a service with the registry.
        
        Args:
            service_id: Unique identifier for the service
            service_info: Service metadata including capabilities, schemas, etc.
            
        Raises:
            ValueError: If service_id is invalid
            ConnectionError: If registration failed
        """
        ...

    async def deregister_service(self, service_id: str) -> None:
        """
        Remove a service from the registry.
        
        Args:
            service_id: Unique identifier for the service to remove
            
        Raises:
            ValueError: If service_id is invalid
            ConnectionError: If deregistration failed
        """
        ...

    async def discover_services(
        self, 
        tags: Optional[List[str]] = None,
        capability: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        Discover services matching the given criteria.
        
        Args:
            tags: Optional list of tags to filter by
            capability: Optional capability to filter by
            
        Returns:
            List of service information dictionaries
            
        Raises:
            ConnectionError: If discovery failed
        """
        ...

    async def get_service(self, service_id: str) -> Optional[Dict[str, Any]]:
        """
        Get information about a specific service.
        
        Args:
            service_id: Unique identifier for the service
            
        Returns:
            Service information dictionary or None if not found
            
        Raises:
            ConnectionError: If lookup failed
        """
        ...
