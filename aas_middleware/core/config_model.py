"""
Configuration model for the middleware system.

This module defines the configuration structures used to configure
the middleware system and its components.
"""

from typing import Dict, Any, List, Optional, Literal
from pydantic import BaseModel, Field
from dataclasses import dataclass


class PersistenceBackendSpec(BaseModel):
    """Specification for a persistence backend."""
    
    kind: Literal["memory", "sql", "redis", "http"] = "memory"
    options: Dict[str, Any] = Field(default_factory=dict)
    
    class Config:
        extra = "forbid"


class ConnectorSpec(BaseModel):
    """Specification for a connector."""
    
    id: str
    kind: str
    options: Dict[str, Any] = Field(default_factory=dict)
    enabled: bool = True
    
    class Config:
        extra = "forbid"


class MapperSpec(BaseModel):
    """Specification for a mapper."""
    
    id: str
    kind: str
    options: Dict[str, Any] = Field(default_factory=dict)
    enabled: bool = True
    
    class Config:
        extra = "forbid"


class FormatterSpec(BaseModel):
    """Specification for a formatter."""
    
    id: str
    kind: str
    options: Dict[str, Any] = Field(default_factory=dict)
    enabled: bool = True
    
    class Config:
        extra = "forbid"


class WorkflowSpec(BaseModel):
    """Specification for a workflow."""
    
    id: str
    kind: str
    options: Dict[str, Any] = Field(default_factory=dict)
    enabled: bool = True
    
    class Config:
        extra = "forbid"


class BindingSpec(BaseModel):
    """Specification for a binding."""
    
    id: str
    source: str
    target: str
    direction: Literal["push", "pull", "bidirectional"] = "push"
    mapper_id: Optional[str] = None
    formatter_id: Optional[str] = None
    enabled: bool = True
    
    class Config:
        extra = "forbid"


class ChainStepSpec(BaseModel):
    """Specification for a chain step."""
    
    type: Literal["receive", "provide", "consume", "map", "format", "call_workflow"]
    id: str
    connector_id: Optional[str] = None
    mapper_id: Optional[str] = None
    formatter_id: Optional[str] = None
    formatter_mode: Optional[Literal["serialize", "deserialize"]] = None
    workflow_id: Optional[str] = None
    options: Dict[str, Any] = Field(default_factory=dict)
    
    class Config:
        extra = "forbid"


class ChainSpec(BaseModel):
    """Specification for a chain."""
    
    id: str
    steps: List[ChainStepSpec]
    enabled: bool = True
    
    class Config:
        extra = "forbid"


class DataModelSpec(BaseModel):
    """Specification for a data model."""
    
    name: str
    types: List[str]  # List of type references or schema definitions
    options: Dict[str, Any] = Field(default_factory=dict)
    
    class Config:
        extra = "forbid"


class DiscoverySpec(BaseModel):
    """Specification for service discovery."""
    
    kind: Literal["consul", "etcd", "kubernetes"] = "consul"
    options: Dict[str, Any] = Field(default_factory=dict)
    enabled: bool = True
    
    class Config:
        extra = "forbid"


class AppConfig(BaseModel):
    """Complete application configuration."""
    
    metadata: Dict[str, Any] = Field(default_factory=dict)
    persistence: PersistenceBackendSpec = Field(default_factory=PersistenceBackendSpec)
    connectors: List[ConnectorSpec] = Field(default_factory=list)
    mappers: List[MapperSpec] = Field(default_factory=list)
    formatters: List[FormatterSpec] = Field(default_factory=list)
    workflows: List[WorkflowSpec] = Field(default_factory=list)
    bindings: List[BindingSpec] = Field(default_factory=list)
    chains: List[ChainSpec] = Field(default_factory=list)
    models: List[DataModelSpec] = Field(default_factory=list)
    discovery: DiscoverySpec = Field(default_factory=DiscoverySpec)
    
    class Config:
        extra = "forbid"
        
    def get_component_spec(self, component_type: str, component_id: str):
        """
        Get a component specification by type and ID.
        
        Args:
            component_type: Type of component
            component_id: ID of the component
            
        Returns:
            Component specification or None if not found
        """
        component_map = {
            "connector": self.connectors,
            "mapper": self.mappers,
            "formatter": self.formatters,
            "workflow": self.workflows,
            "binding": self.bindings,
            "chain": self.chains,
            "model": self.models
        }
        
        if component_type not in component_map:
            return None
            
        components = component_map[component_type]
        for component in components:
            if component.id == component_id:
                return component
                
        return None
        
    def add_component(self, component_type: str, component_spec):
        """
        Add a component specification.
        
        Args:
            component_type: Type of component
            component_spec: Component specification to add
            
        Raises:
            ValueError: If component_type is invalid
        """
        component_map = {
            "connector": self.connectors,
            "mapper": self.mappers,
            "formatter": self.formatters,
            "workflow": self.workflows,
            "binding": self.bindings,
            "chain": self.chains,
            "model": self.models
        }
        
        if component_type not in component_map:
            raise ValueError(f"Invalid component type: {component_type}")
            
        # Remove existing component with same ID
        existing_components = component_map[component_type]
        existing_components[:] = [c for c in existing_components if c.id != component_spec.id]
        
        # Add new component
        existing_components.append(component_spec)
