"""
Binding system for connecting middleware components.

This module defines the binding system that connects connectors, mappers,
and formatters to create data flow paths.
"""

from dataclasses import dataclass
from typing import Optional, List, Dict
from enum import Enum


class BindingDirection(Enum):
    """Direction of data flow in a binding."""
    PUSH = "push"           # Source pushes to target
    PULL = "pull"           # Target pulls from source
    BIDIRECTIONAL = "bidirectional"  # Both directions


@dataclass(frozen=True)
class Address:
    """
    Address for identifying data locations in the system.
    
    This class provides a hierarchical way to identify where data is located
    or should be routed to.
    """
    data_model: str
    model_id: Optional[str] = None
    contained_id: Optional[str] = None
    field: Optional[str] = None
    
    def __str__(self) -> str:
        """String representation of the address."""
        parts = [self.data_model]
        if self.model_id:
            parts.append(self.model_id)
        if self.contained_id:
            parts.append(self.contained_id)
        if self.field:
            parts.append(self.field)
        return "/".join(parts)
    
    @classmethod
    def parse(cls, address_str: str) -> "Address":
        """
        Parse an address string into an Address object.
        
        Args:
            address_str: String representation of the address
            
        Returns:
            Address object
            
        Raises:
            ValueError: If the address string is invalid
        """
        parts = address_str.split("/")
        if len(parts) < 1:
            raise ValueError("Address must have at least a data_model")
            
        data_model = parts[0]
        model_id = parts[1] if len(parts) > 1 else None
        contained_id = parts[2] if len(parts) > 2 else None
        field = parts[3] if len(parts) > 3 else None
        
        return cls(
            data_model=data_model,
            model_id=model_id,
            contained_id=contained_id,
            field=field
        )


@dataclass(frozen=True)
class Binding:
    """
    Binding between source and target components.
    
    A binding defines how data flows from a source to a target,
    optionally applying mappers and formatters along the way.
    """
    id: str
    source: str             # e.g., "connector:erp" or "persist:shop/Order.plan"
    target: str
    direction: BindingDirection
    mapper_id: Optional[str] = None
    formatter_id: Optional[str] = None
    enabled: bool = True
    
    def __post_init__(self):
        """Validate the binding after initialization."""
        if not self.source or not self.target:
            raise ValueError("Source and target must be specified")
        if self.source == self.target:
            raise ValueError("Source and target cannot be the same")


class BindingRegistry:
    """Registry for managing bindings between components."""
    
    def __init__(self):
        self._bindings: Dict[str, Binding] = {}
        
    def add(self, binding: Binding) -> None:
        """
        Add a binding to the registry.
        
        Args:
            binding: The binding to add
            
        Raises:
            ValueError: If binding ID already exists
        """
        if binding.id in self._bindings:
            raise ValueError(f"Binding {binding.id} already exists")
            
        self._bindings[binding.id] = binding
        
    def get(self, binding_id: str) -> Optional[Binding]:
        """
        Get a binding by ID.
        
        Args:
            binding_id: ID of the binding to retrieve
            
        Returns:
            The binding or None if not found
        """
        return self._bindings.get(binding_id)
        
    def remove(self, binding_id: str) -> bool:
        """
        Remove a binding from the registry.
        
        Args:
            binding_id: ID of the binding to remove
            
        Returns:
            True if binding was removed, False if not found
        """
        if binding_id in self._bindings:
            del self._bindings[binding_id]
            return True
        return False
        
    def list(self) -> List[Binding]:
        """
        List all bindings in the registry.
        
        Returns:
            List of all bindings
        """
        return list(self._bindings.values())
        
    def find_by_source(self, source: str) -> List[Binding]:
        """
        Find bindings by source.
        
        Args:
            source: Source identifier
            
        Returns:
            List of bindings with the given source
        """
        return [b for b in self._bindings.values() if b.source == source]
        
    def find_by_target(self, target: str) -> List[Binding]:
        """
        Find bindings by target.
        
        Args:
            target: Target identifier
            
        Returns:
            List of bindings with the given target
        """
        return [b for b in self._bindings.values() if b.target == target]
        
    def find_enabled(self) -> List[Binding]:
        """
        Find all enabled bindings.
        
        Returns:
            List of enabled bindings
        """
        return [b for b in self._bindings.values() if b.enabled]
        
    def clear(self) -> None:
        """Remove all bindings from the registry."""
        self._bindings.clear()
