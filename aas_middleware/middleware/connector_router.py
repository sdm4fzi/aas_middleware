from typing import Any, Dict, List, Optional, Type, Union

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from aas_middleware.connect.connectors.connector import Connector, Consumer, Provider
from aas_middleware.middleware.registries import ConnectionInfo

class ConnectorDescription(BaseModel):
    connector_id: str
    connector_type: str
    persistence_connection: Optional[ConnectionInfo]
    model_type: str


def generate_persistence_connector_endpoint(connector_id: str, connector: Union[Consumer, Provider, Connector], connection_info: ConnectionInfo, model_type: Type[Any]) -> List[APIRouter]:
    """
    Generates endpoints for a workflow to execute the workflow.

    Args:
        workflow (Workflow): Workflow that contains the function to be executed by the workflow.

    Returns:
        APIRouter: FastAPI router with an endpoint to execute the workflow.
    """
    router = APIRouter(
        prefix=f"/connectors/{connector_id}",
        tags=["connectors"],
        responses={404: {"description": "Not found"}},
    )
 
    @router.get("/description", response_model=ConnectorDescription)
    async def describe_connector():
        return ConnectorDescription(
            connector_id=connector_id,
            connector_type=type(connector).__name__,
            persistence_connection=connection_info,
            model_type=model_type.__name__
        )

    if isinstance(connector, Consumer):
        @router.post("/value", response_model=Dict[str, str])
        async def set_value(value: Optional[model_type]=None):
            try:
                await connector.consume(value)
            except ConnectionError as e:
                raise HTTPException(status_code=500, detail=str(e))
            if not value:
                return {"message": f"Set for {connector_id} persistence value."}
            return {"message": f"Set for {connector_id} value {value}"}
        
    if isinstance(connector, Provider):
        @router.get("/value", response_model=model_type)
        async def get_value():
            try:
                return await connector.provide()
            except ConnectionError as e:
                raise HTTPException(status_code=500, detail=str(e))
            
    return router


def generate_connector_endpoint(connector_id: str, connector: Union[Consumer, Provider, Connector], model_type: Type[Any]) -> List[APIRouter]:
    """
    Generates endpoints for a workflow to execute the workflow.

    Args:
        workflow (Workflow): Workflow that contains the function to be executed by the workflow.

    Returns:
        APIRouter: FastAPI router with an endpoint to execute the workflow.
    """
    router = APIRouter(
        prefix=f"/connectors/{connector_id}",
        tags=["connectors"],
        responses={404: {"description": "Not found"}},
    )
 
    @router.get("/description", response_model=ConnectorDescription)
    async def describe_connector():
        return ConnectorDescription(
            connector_id=connector_id,
            connector_type=type(connector).__name__,
            persistence_connection=None,
            model_type=model_type.__name__
        )

    if isinstance(connector, Consumer):
        @router.post("/value", response_model=Dict[str, str])
        async def set_value(value: model_type):
            try:
                await connector.consume(value)
            except ConnectionError as e:
                raise HTTPException(status_code=500, detail=str(e))
            return {"message": f"Set value for {connector_id}"}
        
    if isinstance(connector, Provider):
        @router.get("/value", response_model=model_type)
        async def get_value():
            try:
                return await connector.provide()
            except ConnectionError as e:
                raise HTTPException(status_code=500, detail=str(e))

    return router
