"""
Registry system for managing middleware components.

This module provides registries for connectors, mappers, formatters, and workflows,
enabling component discovery and management.
"""

from typing import Dict, Any, Optional, List, TypeVar, Generic
from .errors import RegistryError
import logging

logger = logging.getLogger(__name__)

T = TypeVar("T")

class BaseRegistry(Generic[T]):
    """Base class for component registries."""
    
    def __init__(self, name: str):
        self.name = name
        self._components: Dict[str, T] = {}
        
    def add(self, component_id: str, component: T) -> None:
        """
        Add a component to the registry.
        
        Args:
            component_id: Unique identifier for the component
            component: The component instance
            
        Raises:
            RegistryError: If component_id already exists
        """
        if component_id in self._components:
            raise RegistryError(f"Component {component_id} already exists in {self.name}")
            
        self._components[component_id] = component
        logger.info(f"Added {component_id} to {self.name}")
        
    def get(self, component_id: str) -> Optional[T]:
        """
        Get a component by ID.
        
        Args:
            component_id: Unique identifier for the component
            
        Returns:
            The component instance or None if not found
        """
        return self._components.get(component_id)
        
    def remove(self, component_id: str) -> bool:
        """
        Remove a component from the registry.
        
        Args:
            component_id: Unique identifier for the component
            
        Returns:
            True if component was removed, False if not found
        """
        if component_id in self._components:
            del self._components[component_id]
            logger.info(f"Removed {component_id} from {self.name}")
            return True
        return False
        
    def list(self) -> List[str]:
        """
        List all component IDs in the registry.
        
        Returns:
            List of component IDs
        """
        return list(self._components.keys())
        
    def count(self) -> int:
        """
        Get the number of components in the registry.
        
        Returns:
            Number of components
        """
        return len(self._components)
        
    def clear(self) -> None:
        """Remove all components from the registry."""
        self._components.clear()
        logger.info(f"Cleared {self.name}")


class ConnectorRegistry(BaseRegistry):
    """Registry for managing connectors."""
    
    def __init__(self):
        super().__init__("ConnectorRegistry")


class MapperRegistry(BaseRegistry):
    """Registry for managing mappers."""
    
    def __init__(self):
        super().__init__("MapperRegistry")


class FormatterRegistry(BaseRegistry):
    """Registry for managing formatters."""
    
    def __init__(self):
        super().__init__("FormatterRegistry")


class WorkflowRegistry(BaseRegistry):
    """Registry for managing workflows."""
    
    def __init__(self):
        super().__init__("WorkflowRegistry")


class RegistryManager:
    """Manages all component registries."""
    
    def __init__(self):
        self.connectors = ConnectorRegistry()
        self.mappers = MapperRegistry()
        self.formatters = FormatterRegistry()
        self.workflows = WorkflowRegistry()
        
    def get_registry(self, component_type: str):
        """
        Get a registry by component type.
        
        Args:
            component_type: Type of component ("connector", "mapper", "formatter", "workflow")
            
        Returns:
            The appropriate registry
            
        Raises:
            ValueError: If component_type is invalid
        """
        registry_map = {
            "connector": self.connectors,
            "mapper": self.mappers,
            "formatter": self.formatters,
            "workflow": self.workflows
        }
        
        if component_type not in registry_map:
            raise ValueError(f"Invalid component type: {component_type}")
            
        return registry_map[component_type]
        
    def list_all_components(self) -> Dict[str, List[str]]:
        """
        List all components across all registries.
        
        Returns:
            Dictionary mapping component types to lists of component IDs
        """
        return {
            "connectors": self.connectors.list(),
            "mappers": self.mappers.list(),
            "formatters": self.formatters.list(),
            "workflows": self.workflows.list()
        }
        
    def clear_all(self) -> None:
        """Clear all registries."""
        self.connectors.clear()
        self.mappers.clear()
        self.formatters.clear()
        self.workflows.clear()
        logger.info("Cleared all registries")
