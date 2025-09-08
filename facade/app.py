"""
Main middleware application class.

This module provides the main application class that orchestrates
all the middleware components and provides the runtime environment.
"""

from typing import Dict, Any, Optional
from ..core.config_model import AppConfig
from ..core.registries import RegistryManager
from ..core.events import EventBus
from ..core.instrumentation import instrument_connector
import logging
import asyncio

logger = logging.getLogger(__name__)

class MiddlewareApp:
    """
    Main middleware application.
    
    This class orchestrates all middleware components and provides
    the runtime environment for the system.
    """
    
    def __init__(self, config: AppConfig, registries: RegistryManager):
        """
        Initialize the middleware application.
        
        Args:
            config: Application configuration
            registries: Component registries
        """
        self.config = config
        self.registries = registries
        self.event_bus = EventBus()
        self._running = False
        self._tasks = []
        
    async def start(self) -> None:
        """Start the middleware application."""
        if self._running:
            logger.warning("Middleware application already running")
            return
            
        logger.info("Starting middleware application")
        
        try:
            # Initialize components
            await self._initialize_components()
            
            # Start background tasks
            await self._start_background_tasks()
            
            self._running = True
            logger.info("Middleware application started successfully")
            
        except Exception as e:
            logger.error(f"Failed to start middleware application: {e}")
            raise
            
    async def stop(self) -> None:
        """Stop the middleware application."""
        if not self._running:
            logger.warning("Middleware application not running")
            return
            
        logger.info("Stopping middleware application")
        
        try:
            # Stop background tasks
            await self._stop_background_tasks()
            
            # Cleanup components
            await self._cleanup_components()
            
            self._running = False
            logger.info("Middleware application stopped successfully")
            
        except Exception as e:
            logger.error(f"Error stopping middleware application: {e}")
            raise
            
    async def _initialize_components(self) -> None:
        """Initialize all components based on configuration."""
        logger.info("Initializing components")
        
        # Initialize connectors
        for connector_spec in self.config.connectors:
            if connector_spec.enabled:
                await self._initialize_connector(connector_spec)
                
        # Initialize mappers
        for mapper_spec in self.config.mappers:
            if mapper_spec.enabled:
                await self._initialize_mapper(mapper_spec)
                
        # Initialize formatters
        for formatter_spec in self.config.formatters:
            if formatter_spec.enabled:
                await self._initialize_formatter(formatter_spec)
                
        # Initialize workflows
        for workflow_spec in self.config.workflows:
            if workflow_spec.enabled:
                await self._initialize_workflow(workflow_spec)
                
        logger.info("Components initialized")
        
    async def _initialize_connector(self, connector_spec) -> None:
        """Initialize a connector based on its specification."""
        try:
            # Create connector instance based on kind
            connector = await self._create_connector(connector_spec)
            
            # Wrap with instrumentation
            instrumented_connector = instrument_connector(
                connector, 
                connector_spec.id, 
                self.event_bus
            )
            
            # Register in registry
            self.registries.connectors.add(connector_spec.id, instrumented_connector)
            
            # Connect if it supports lifecycle
            if hasattr(instrumented_connector, 'connect'):
                await instrumented_connector.connect()
                
            logger.info(f"Initialized connector: {connector_spec.id}")
            
        except Exception as e:
            logger.error(f"Failed to initialize connector {connector_spec.id}: {e}")
            raise
            
    async def _create_connector(self, connector_spec) -> Any:
        """Create a connector instance based on its specification."""
        # This is a simplified implementation
        # In a real system, you would have a factory system
        # that creates connectors based on kind and options
        
        if connector_spec.kind == "memory":
            from ..adapters.connectors.memory_connector import MemoryConnector
            return MemoryConnector("default", "default")
        elif connector_spec.kind == "http_in":
            # Create HTTP input connector
            # This would be implemented based on the specific connector type
            raise NotImplementedError(f"Connector kind '{connector_spec.kind}' not implemented")
        elif connector_spec.kind == "http_out":
            # Create HTTP output connector
            raise NotImplementedError(f"Connector kind '{connector_spec.kind}' not implemented")
        else:
            raise ValueError(f"Unknown connector kind: {connector_spec.kind}")
            
    async def _initialize_mapper(self, mapper_spec) -> None:
        """Initialize a mapper based on its specification."""
        try:
            # Create mapper instance based on kind
            mapper = await self._create_mapper(mapper_spec)
            
            # Register in registry
            self.registries.mappers.add(mapper_spec.id, mapper)
            
            logger.info(f"Initialized mapper: {mapper_spec.id}")
            
        except Exception as e:
            logger.error(f"Failed to initialize mapper {mapper_spec.id}: {e}")
            raise
            
    async def _create_mapper(self, mapper_spec) -> Any:
        """Create a mapper instance based on its specification."""
        # This is a simplified implementation
        # In a real system, you would have a factory system
        raise NotImplementedError(f"Mapper creation not implemented")
        
    async def _initialize_formatter(self, formatter_spec) -> None:
        """Initialize a formatter based on its specification."""
        try:
            # Create formatter instance based on kind
            formatter = await self._create_formatter(formatter_spec)
            
            # Register in registry
            self.registries.formatters.add(formatter_spec.id, formatter)
            
            logger.info(f"Initialized formatter: {formatter_spec.id}")
            
        except Exception as e:
            logger.error(f"Failed to initialize formatter {formatter_spec.id}: {e}")
            raise
            
    async def _create_formatter(self, formatter_spec) -> Any:
        """Create a formatter instance based on its specification."""
        # This is a simplified implementation
        # In a real system, you would have a factory system
        raise NotImplementedError(f"Formatter creation not implemented")
        
    async def _initialize_workflow(self, workflow_spec) -> None:
        """Initialize a workflow based on its specification."""
        try:
            # Create workflow instance based on kind
            workflow = await self._create_workflow(workflow_spec)
            
            # Register in registry
            self.registries.workflows.add(workflow_spec.id, workflow)
            
            logger.info(f"Initialized workflow: {workflow_spec.id}")
            
        except Exception as e:
            logger.error(f"Failed to initialize workflow {workflow_spec.id}: {e}")
            raise
            
    async def _create_workflow(self, workflow_spec) -> Any:
        """Create a workflow instance based on its specification."""
        # This is a simplified implementation
        # In a real system, you would have a factory system
        raise NotImplementedError(f"Workflow creation not implemented")
        
    async def _start_background_tasks(self) -> None:
        """Start background tasks for the application."""
        logger.info("Starting background tasks")
        
        # Start sync engine if bindings are configured
        if self.config.bindings:
            # This would start the synchronization engine
            # that manages data flow between connectors
            pass
            
        # Start service discovery if configured
        if self.config.discovery.enabled:
            # This would start the service discovery system
            pass
            
        logger.info("Background tasks started")
        
    async def _stop_background_tasks(self) -> None:
        """Stop background tasks for the application."""
        logger.info("Stopping background tasks")
        
        # Cancel all running tasks
        for task in self._tasks:
            if not task.done():
                task.cancel()
                
        # Wait for tasks to complete
        if self._tasks:
            await asyncio.gather(*self._tasks, return_exceptions=True)
            
        self._tasks.clear()
        logger.info("Background tasks stopped")
        
    async def _cleanup_components(self) -> None:
        """Cleanup all components."""
        logger.info("Cleaning up components")
        
        # Disconnect connectors
        for connector_id in self.registries.connectors.list():
            connector = self.registries.connectors.get(connector_id)
            if connector and hasattr(connector, 'disconnect'):
                try:
                    await connector.disconnect()
                except Exception as e:
                    logger.warning(f"Error disconnecting connector {connector_id}: {e}")
                    
        logger.info("Components cleaned up")
        
    @property
    def running(self) -> bool:
        """Check if the application is running."""
        return self._running
        
    def get_status(self) -> Dict[str, Any]:
        """
        Get the current status of the application.
        
        Returns:
            Dictionary containing application status
        """
        return {
            "running": self._running,
            "config": self.config.dict(),
            "components": self.registries.list_all_components(),
            "events": self.event_bus.get_event_history(limit=10)
        }
        
    async def run_chain(self, chain_id: str, input_data: Any = None) -> Any:
        """
        Run a chain with optional input data.
        
        Args:
            chain_id: ID of the chain to run
            input_data: Optional input data for the chain
            
        Returns:
            Chain execution result
            
        Raises:
            ValueError: If chain not found
        """
        chain_spec = self.config.get_component_spec("chain", chain_id)
        if not chain_spec:
            raise ValueError(f"Chain not found: {chain_id}")
            
        # This would execute the chain based on its specification
        # For now, just log the request
        logger.info(f"Running chain: {chain_id}")
        
        # Emit chain execution event
        self.event_bus.publish(
            "chain.execute",
            data={"chain_id": chain_id, "input_data": input_data},
            source="system"
        )
        
        # Placeholder for actual chain execution
        return {"status": "executed", "chain_id": chain_id}
