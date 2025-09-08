import asyncio
import json
import logging
from typing import Any, Dict, List, Optional, Union
from datetime import datetime

from fastapi import FastAPI, HTTPException, BackgroundTasks, Depends
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
import uvicorn

from aas_middleware.facade.app import MiddlewareApp
from aas_middleware.core.errors import MiddlewareError
from aas_middleware.domain.data_model import DataModel
from aas_middleware.adapters.connectors import (
    MemoryConnector, HttpInConnector, HttpOutConnector, HttpConnectorConfig,
    SqlConnector, SqlConnectorConfig, RedisConnector, RedisConnectorConfig
)

logger = logging.getLogger(__name__)


class ConnectorRequest(BaseModel):
    """Request model for connector operations."""
    connector_id: str = Field(..., description="Connector identifier")
    data: Optional[Dict[str, Any]] = Field(default=None, description="Data to consume")
    meta: Optional[Dict[str, Any]] = Field(default=None, description="Metadata")


class ConnectorResponse(BaseModel):
    """Response model for connector operations."""
    success: bool = Field(..., description="Operation success status")
    data: Optional[Dict[str, Any]] = Field(default=None, description="Retrieved data")
    message: str = Field(..., description="Response message")
    timestamp: str = Field(default_factory=lambda: datetime.utcnow().isoformat())


class ConnectorStatus(BaseModel):
    """Status model for connector information."""
    connector_id: str = Field(..., description="Connector identifier")
    type: str = Field(..., description="Connector type")
    connected: bool = Field(..., description="Connection status")
    data_model: str = Field(..., description="Data model class name")
    config: Dict[str, Any] = Field(..., description="Connector configuration")


class MiddlewareRestAPI:
    """REST API middleware for external connector operations."""
    
    def __init__(self, app: MiddlewareApp):
        self.app = app
        self.fastapi_app = FastAPI(
            title="AAS Middleware REST API",
            description="REST API for AAS Middleware connector operations",
            version="1.0.0"
        )
        
        # Add CORS middleware
        self.fastapi_app.add_middleware(
            CORSMiddleware,
            allow_origins=["*"],
            allow_credentials=True,
            allow_methods=["*"],
            allow_headers=["*"],
        )
        
        self._setup_routes()
    
    def _setup_routes(self):
        """Setup FastAPI routes."""
        
        @self.fastapi_app.get("/")
        async def root():
            """Root endpoint."""
            return {"message": "AAS Middleware REST API", "version": "1.0.0"}
        
        @self.fastapi_app.get("/health")
        async def health():
            """Health check endpoint."""
            try:
                status = self.app.get_status()
                return {
                    "status": "healthy",
                    "running": status.get("running", False),
                    "components": status.get("components", {}),
                    "timestamp": datetime.utcnow().isoformat()
                }
            except Exception as e:
                logger.error(f"Health check failed: {e}")
                raise HTTPException(status_code=500, detail=str(e))
        
        @self.fastapi_app.get("/connectors")
        async def list_connectors():
            """List all registered connectors."""
            try:
                connectors = self.app.connector_registry.list()
                connector_statuses = []
                
                for connector_id, connector in connectors.items():
                    status = ConnectorStatus(
                        connector_id=connector_id,
                        type=connector.__class__.__name__,
                        connected=getattr(connector, '_connected', False) or 
                                getattr(connector, '_session', None) is not None or
                                getattr(connector, '_pool', None) is not None or
                                getattr(connector, '_redis', None) is not None,
                        data_model=connector.data_model.__name__,
                        config=getattr(connector, 'config', {}).dict() if hasattr(connector, 'config') else {}
                    )
                    connector_statuses.append(status)
                
                return {"connectors": connector_statuses}
            except Exception as e:
                logger.error(f"Failed to list connectors: {e}")
                raise HTTPException(status_code=500, detail=str(e))
        
        @self.fastapi_app.get("/connectors/{connector_id}")
        async def get_connector_status(connector_id: str):
            """Get status of a specific connector."""
            try:
                connector = self.app.connector_registry.get(connector_id)
                if not connector:
                    raise HTTPException(status_code=404, detail=f"Connector {connector_id} not found")
                
                status = ConnectorStatus(
                    connector_id=connector_id,
                    type=connector.__class__.__name__,
                    connected=getattr(connector, '_connected', False) or 
                            getattr(connector, '_session', None) is not None or
                            getattr(connector, '_pool', None) is not None or
                            getattr(connector, '_redis', None) is not None,
                    data_model=connector.data_model.__name__,
                    config=getattr(connector, 'config', {}).dict() if hasattr(connector, 'config') else {}
                )
                
                return status
            except HTTPException:
                raise
            except Exception as e:
                logger.error(f"Failed to get connector status: {e}")
                raise HTTPException(status_code=500, detail=str(e))
        
        @self.fastapi_app.post("/connectors/{connector_id}/connect")
        async def connect_connector(connector_id: str):
            """Connect a specific connector."""
            try:
                connector = self.app.connector_registry.get(connector_id)
                if not connector:
                    raise HTTPException(status_code=404, detail=f"Connector {connector_id} not found")
                
                if hasattr(connector, 'connect'):
                    await connector.connect()
                    return {"message": f"Connector {connector_id} connected successfully"}
                else:
                    return {"message": f"Connector {connector_id} does not support connection management"}
            except Exception as e:
                logger.error(f"Failed to connect connector {connector_id}: {e}")
                raise HTTPException(status_code=500, detail=str(e))
        
        @self.fastapi_app.post("/connectors/{connector_id}/disconnect")
        async def disconnect_connector(connector_id: str):
            """Disconnect a specific connector."""
            try:
                connector = self.app.connector_registry.get(connector_id)
                if not connector:
                    raise HTTPException(status_code=404, detail=f"Connector {connector_id} not found")
                
                if hasattr(connector, 'disconnect'):
                    await connector.disconnect()
                    return {"message": f"Connector {connector_id} disconnected successfully"}
                else:
                    return {"message": f"Connector {connector_id} does not support connection management"}
            except Exception as e:
                logger.error(f"Failed to disconnect connector {connector_id}: {e}")
                raise HTTPException(status_code=500, detail=str(e))
        
        @self.fastapi_app.get("/connectors/{connector_id}/provide")
        async def provide_data(connector_id: str):
            """Provide data from a specific connector."""
            try:
                connector = self.app.connector_registry.get(connector_id)
                if not connector:
                    raise HTTPException(status_code=404, detail=f"Connector {connector_id} not found")
                
                data = await connector.provide()
                
                return ConnectorResponse(
                    success=True,
                    data=data.to_dict() if data else None,
                    message=f"Data provided from connector {connector_id}"
                )
            except Exception as e:
                logger.error(f"Failed to provide data from connector {connector_id}: {e}")
                return ConnectorResponse(
                    success=False,
                    message=f"Failed to provide data: {str(e)}"
                )
        
        @self.fastapi_app.post("/connectors/{connector_id}/consume")
        async def consume_data(connector_id: str, request: ConnectorRequest):
            """Consume data to a specific connector."""
            try:
                connector = self.app.connector_registry.get(connector_id)
                if not connector:
                    raise HTTPException(status_code=404, detail=f"Connector {connector_id} not found")
                
                if not request.data:
                    raise HTTPException(status_code=400, detail="Data is required for consumption")
                
                # Create data model instance
                data_model_class = connector.data_model
                data_instance = data_model_class.from_dict(request.data)
                
                # Consume data
                await connector.consume(data_instance, meta=request.meta)
                
                return ConnectorResponse(
                    success=True,
                    message=f"Data consumed by connector {connector_id}"
                )
            except Exception as e:
                logger.error(f"Failed to consume data to connector {connector_id}: {e}")
                return ConnectorResponse(
                    success=False,
                    message=f"Failed to consume data: {str(e)}"
                )
        
        @self.fastapi_app.get("/connectors/{connector_id}/receive")
        async def receive_data_stream(connector_id: str, limit: int = 10):
            """Receive data stream from a specific connector."""
            try:
                connector = self.app.connector_registry.get(connector_id)
                if not connector:
                    raise HTTPException(status_code=404, detail=f"Connector {connector_id} not found")
                
                # For streaming, we'll collect a limited number of items
                received_data = []
                async for data in connector.receive():
                    received_data.append(data.to_dict())
                    if len(received_data) >= limit:
                        break
                
                return ConnectorResponse(
                    success=True,
                    data={"items": received_data, "count": len(received_data)},
                    message=f"Received {len(received_data)} items from connector {connector_id}"
                )
            except Exception as e:
                logger.error(f"Failed to receive data from connector {connector_id}: {e}")
                return ConnectorResponse(
                    success=False,
                    message=f"Failed to receive data: {str(e)}"
                )
        
        @self.fastapi_app.post("/connectors/{connector_id}/clear")
        async def clear_connector_data(connector_id: str):
            """Clear data from a specific connector."""
            try:
                connector = self.app.connector_registry.get(connector_id)
                if not connector:
                    raise HTTPException(status_code=404, detail=f"Connector {connector_id} not found")
                
                if hasattr(connector, 'clear'):
                    await connector.clear()
                    return {"message": f"Data cleared from connector {connector_id}"}
                else:
                    return {"message": f"Connector {connector_id} does not support clearing data"}
            except Exception as e:
                logger.error(f"Failed to clear data from connector {connector_id}: {e}")
                raise HTTPException(status_code=500, detail=str(e))
        
        @self.fastapi_app.get("/connectors/{connector_id}/count")
        async def get_connector_count(connector_id: str):
            """Get count of data items in a specific connector."""
            try:
                connector = self.app.connector_registry.get(connector_id)
                if not connector:
                    raise HTTPException(status_code=404, detail=f"Connector {connector_id} not found")
                
                if hasattr(connector, 'count'):
                    count = await connector.count()
                    return {"connector_id": connector_id, "count": count}
                else:
                    return {"message": f"Connector {connector_id} does not support counting data"}
            except Exception as e:
                logger.error(f"Failed to get count from connector {connector_id}: {e}")
                raise HTTPException(status_code=500, detail=str(e))
        
        @self.fastapi_app.post("/workflows/run")
        async def run_workflow(workflow_id: str, background_tasks: BackgroundTasks):
            """Run a workflow in the background."""
            try:
                workflow = self.app.workflow_registry.get(workflow_id)
                if not workflow:
                    raise HTTPException(status_code=404, detail=f"Workflow {workflow_id} not found")
                
                # Add workflow execution to background tasks
                background_tasks.add_task(self.app.run_workflow, workflow_id)
                
                return {"message": f"Workflow {workflow_id} started in background"}
            except Exception as e:
                logger.error(f"Failed to start workflow {workflow_id}: {e}")
                raise HTTPException(status_code=500, detail=str(e))
        
        @self.fastapi_app.get("/workflows")
        async def list_workflows():
            """List all registered workflows."""
            try:
                workflows = self.app.workflow_registry.list()
                return {"workflows": list(workflows.keys())}
            except Exception as e:
                logger.error(f"Failed to list workflows: {e}")
                raise HTTPException(status_code=500, detail=str(e))
        
        @self.fastapi_app.get("/bindings")
        async def list_bindings():
            """List all registered bindings."""
            try:
                bindings = self.app.binding_registry.list()
                return {"bindings": [binding.dict() for binding in bindings]}
            except Exception as e:
                logger.error(f"Failed to list bindings: {e}")
                raise HTTPException(status_code=500, detail=str(e))
    
    def get_app(self) -> FastAPI:
        """Get the FastAPI application instance."""
        return self.fastapi_app
    
    async def start(self, host: str = "0.0.0.0", port: int = 8000):
        """Start the REST API server."""
        config = uvicorn.Config(
            app=self.fastapi_app,
            host=host,
            port=port,
            log_level="info"
        )
        server = uvicorn.Server(config)
        await server.serve()
    
    def run_sync(self, host: str = "0.0.0.0", port: int = 8000):
        """Run the REST API server synchronously."""
        uvicorn.run(
            app=self.fastapi_app,
            host=host,
            port=port,
            log_level="info"
        )
