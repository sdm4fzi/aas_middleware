"""
Application builder for the middleware system.

This module provides a fluent builder interface for configuring
and building middleware applications.
"""

from typing import List, Optional, Dict, Any
from ..core.config_model import (
    AppConfig, PersistenceBackendSpec, ConnectorSpec, 
    MapperSpec, FormatterSpec, WorkflowSpec, BindingSpec,
    ChainSpec, DataModelSpec, DiscoverySpec
)
from ..core.registries import RegistryManager
from ..core.bindings import Binding, BindingDirection
from ..adapters.connectors.memory_connector import MemoryConnector
import logging

logger = logging.getLogger(__name__)

class AppBuilder:
    """
    Fluent builder for configuring middleware applications.
    
    This class provides a chainable interface for configuring
    all aspects of the middleware system.
    """
    
    def __init__(self):
        """Initialize the app builder."""
        self.config = AppConfig()
        self.registries = RegistryManager()
        self.data_models: Dict[str, Any] = {}
        
    def meta(self, title: str, version: str, **kwargs) -> 'AppBuilder':
        """
        Set application metadata.
        
        Args:
            title: Application title
            version: Application version
            **kwargs: Additional metadata
            
        Returns:
            Self for chaining
        """
        self.config.metadata.update({
            "title": title,
            "version": version,
            **kwargs
        })
        return self
        
    def persistence(self, kind: str = "memory", **options) -> 'AppBuilder':
        """
        Configure the persistence backend.
        
        Args:
            kind: Type of persistence backend
            **options: Backend-specific options
            
        Returns:
            Self for chaining
        """
        self.config.persistence = PersistenceBackendSpec(
            kind=kind,
            options=options
        )
        return self
        
    def models(self, name: str, types: List[str], **options) -> 'AppBuilder':
        """
        Register data models.
        
        Args:
            name: Name of the data model group
            types: List of model type references
            **options: Model-specific options
            
        Returns:
            Self for chaining
        """
        model_spec = DataModelSpec(
            name=name,
            types=types,
            options=options
        )
        self.config.add_component("model", model_spec)
        
        # Auto-create persistence connectors for each model type
        self._create_persistence_connectors(name, types)
        
        return self
        
    def connector(self, id: str, kind: str, **options) -> 'AppBuilder':
        """
        Add a connector.
        
        Args:
            id: Connector identifier
            kind: Type of connector
            **options: Connector-specific options
            
        Returns:
            Self for chaining
        """
        connector_spec = ConnectorSpec(
            id=id,
            kind=kind,
            options=options
        )
        self.config.add_component("connector", connector_spec)
        return self
        
    def mapper(self, id: str, kind: str, **options) -> 'AppBuilder':
        """
        Add a mapper.
        
        Args:
            id: Mapper identifier
            kind: Type of mapper
            **options: Mapper-specific options
            
        Returns:
            Self for chaining
        """
        mapper_spec = MapperSpec(
            id=id,
            kind=kind,
            options=options
        )
        self.config.add_component("mapper", mapper_spec)
        return self
        
    def formatter(self, id: str, kind: str, **options) -> 'AppBuilder':
        """
        Add a formatter.
        
        Args:
            id: Formatter identifier
            kind: Type of formatter
            **options: Formatter-specific options
            
        Returns:
            Self for chaining
        """
        formatter_spec = FormatterSpec(
            id=id,
            kind=kind,
            options=options
        )
        self.config.add_component("formatter", formatter_spec)
        return self
        
    def workflow(self, id: str, kind: str, **options) -> 'AppBuilder':
        """
        Add a workflow.
        
        Args:
            id: Workflow identifier
            kind: Type of workflow
            **options: Workflow-specific options
            
        Returns:
            Self for chaining
        """
        workflow_spec = WorkflowSpec(
            id=id,
            kind=kind,
            options=options
        )
        self.config.add_component("workflow", workflow_spec)
        return self
        
    def bind(self, source: str, target: str, direction: str = "push", 
             mapper_id: Optional[str] = None, formatter_id: Optional[str] = None) -> 'AppBuilder':
        """
        Create a binding between components.
        
        Args:
            source: Source component identifier
            target: Target component identifier
            direction: Binding direction
            mapper_id: Optional mapper to apply
            formatter_id: Optional formatter to apply
            
        Returns:
            Self for chaining
        """
        binding_spec = BindingSpec(
            id=f"binding_{source}_{target}",
            source=source,
            target=target,
            direction=direction,
            mapper_id=mapper_id,
            formatter_id=formatter_id
        )
        self.config.add_component("binding", binding_spec)
        return self
        
    def chain(self, id: str) -> 'ChainBuilder':
        """
        Start building a chain.
        
        Args:
            id: Chain identifier
            
        Returns:
            Chain builder for configuring chain steps
        """
        return ChainBuilder(self, id)
        
    def discover(self, kind: str = "consul", **options) -> 'AppBuilder':
        """
        Configure service discovery.
        
        Args:
            kind: Type of service discovery
            **options: Discovery-specific options
            
        Returns:
            Self for chaining
        """
        discovery_spec = DiscoverySpec(
            kind=kind,
            options=options
        )
        self.config.discovery = discovery_spec
        return self
        
    def expose(self, kind: str, **options) -> 'AppBuilder':
        """
        Configure API exposure.
        
        Args:
            kind: Type of API to expose
            **options: API-specific options
            
        Returns:
            Self for chaining
        """
        # This would be implemented based on the specific API type
        logger.info(f"Exposing {kind} API with options: {options}")
        return self
        
    def serve(self, host: str = "0.0.0.0", port: int = 8000) -> 'AppBuilder':
        """
        Configure the server.
        
        Args:
            host: Host to bind to
            port: Port to bind to
            
        Returns:
            Self for chaining
        """
        self.config.metadata.update({
            "host": host,
            "port": port
        })
        return self
        
    def _create_persistence_connectors(self, model_name: str, types: List[str]) -> None:
        """
        Automatically create persistence connectors for data models.
        
        Args:
            model_name: Name of the data model
            types: List of model types
        """
        for type_name in types:
            # Create connector for the entire model type
            conn_id = f"persist:{model_name}/{type_name}"
            connector = MemoryConnector(model_name, type_name)
            self.registries.connectors.add(conn_id, connector)
            
            # Optionally create field-level connectors for hot fields
            # This would be based on model schema analysis
            logger.info(f"Created persistence connector: {conn_id}")
            
    def build(self) -> 'MiddlewareApp':
        """
        Build the middleware application.
        
        Returns:
            Configured middleware application
        """
        from .app import MiddlewareApp
        return MiddlewareApp(self.config, self.registries)


class ChainBuilder:
    """Builder for configuring chain steps."""
    
    def __init__(self, app_builder: AppBuilder, chain_id: str):
        """
        Initialize the chain builder.
        
        Args:
            app_builder: Parent app builder
            chain_id: Chain identifier
        """
        self.app_builder = app_builder
        self.chain_id = chain_id
        self.steps = []
        
    def receive(self, connector_id: str, **options) -> 'ChainBuilder':
        """
        Add a receive step.
        
        Args:
            connector_id: ID of the connector to receive from
            **options: Step-specific options
            
        Returns:
            Self for chaining
        """
        step = {
            "type": "receive",
            "id": f"rx:{connector_id}",
            "connector_id": connector_id,
            "options": options
        }
        self.steps.append(step)
        return self
        
    def provide(self, connector_id: str, **options) -> 'ChainBuilder':
        """
        Add a provide step.
        
        Args:
            connector_id: ID of the connector to provide from
            **options: Step-specific options
            
        Returns:
            Self for chaining
        """
        step = {
            "type": "provide",
            "id": f"prov:{connector_id}",
            "connector_id": connector_id,
            "options": options
        }
        self.steps.append(step)
        return self
        
    def consume(self, connector_id: str, **options) -> 'ChainBuilder':
        """
        Add a consume step.
        
        Args:
            connector_id: ID of the connector to consume to
            **options: Step-specific options
            
        Returns:
            Self for chaining
        """
        step = {
            "type": "consume",
            "id": f"cons:{connector_id}",
            "connector_id": connector_id,
            "options": options
        }
        self.steps.append(step)
        return self
        
    def map(self, mapper_id: str, **options) -> 'ChainBuilder':
        """
        Add a mapping step.
        
        Args:
            mapper_id: ID of the mapper to use
            **options: Step-specific options
            
        Returns:
            Self for chaining
        """
        step = {
            "type": "map",
            "id": f"map:{mapper_id}",
            "mapper_id": mapper_id,
            "options": options
        }
        self.steps.append(step)
        return self
        
    def format(self, formatter_id: str, mode: str = "serialize", **options) -> 'ChainBuilder':
        """
        Add a formatting step.
        
        Args:
            formatter_id: ID of the formatter to use
            mode: Formatting mode (serialize/deserialize)
            **options: Step-specific options
            
        Returns:
            Self for chaining
        """
        step = {
            "type": "format",
            "id": f"fmt:{formatter_id}",
            "formatter_id": formatter_id,
            "formatter_mode": mode,
            "options": options
        }
        self.steps.append(step)
        return self
        
    def call_workflow(self, workflow_id: str, **options) -> 'ChainBuilder':
        """
        Add a workflow call step.
        
        Args:
            workflow_id: ID of the workflow to call
            **options: Step-specific options
            
        Returns:
            Self for chaining
        """
        step = {
            "type": "call_workflow",
            "id": f"wf:{workflow_id}",
            "workflow_id": workflow_id,
            "options": options
        }
        self.steps.append(step)
        return self
        
    def register(self) -> AppBuilder:
        """
        Register the chain and return to app builder.
        
        Returns:
            Parent app builder for chaining
        """
        # Convert steps to proper format
        from ..core.config_model import ChainStepSpec, ChainSpec
        
        chain_steps = []
        for step_data in self.steps:
            step = ChainStepSpec(**step_data)
            chain_steps.append(step)
            
        chain_spec = ChainSpec(
            id=self.chain_id,
            steps=chain_steps
        )
        
        self.app_builder.config.add_component("chain", chain_spec)
        logger.info(f"Registered chain: {self.chain_id}")
        
        return self.app_builder
