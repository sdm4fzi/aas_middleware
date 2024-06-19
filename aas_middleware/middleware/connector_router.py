from typing import Any, Dict, List, Optional, Type, Union

from fastapi import APIRouter
from pydantic import BaseModel
from aas_middleware.connect.connectors.connector import Connector, Consumer, Provider
from aas_middleware.middleware.registries import ConnectionInfo, PersistenceConnectionRegistry
from aas_middleware.model.data_model import DataModel
from aas_middleware.model.util import get_value_attributes

class ConnectorDescription(BaseModel):
    connector_id: str
    connector_type: str
    persistence_connection: Optional[ConnectionInfo]
    model_type: str


async def update_persistence_with_value(persistence_connector: Connector, connection_info: ConnectionInfo, value: Any):
    if not connection_info.contained_model_id and not connection_info.field_id:
        await persistence_connector.consume(value)
    elif not connection_info.field_id:
        persistence_model = await persistence_connector.provide()
        persistence_model_data_model = DataModel.from_models(persistence_model)
        # TODO: make sure when id changes the connection info changes as well
        persistence_contained_model = persistence_model_data_model.get_model(connection_info.contained_model_id)
        referencing_models = persistence_model_data_model.get_referencing_models(persistence_contained_model)
        for referencing_model in referencing_models:
            for attribute_name, attribute_value in get_value_attributes(referencing_model):
                if attribute_value == persistence_contained_model:
                    setattr(referencing_model, attribute_name, value)
        await persistence_connector.consume(persistence_model)
    elif not connection_info.contained_model_id:
        persistence_model = await persistence_connector.provide()
        setattr(persistence_model, connection_info.field_id, value)
        await persistence_connector.consume(persistence_model)
    else:
        persistence_model = await persistence_connector.provide()
        persistence_model_data_model = DataModel.from_models(persistence_model)
        persistence_contained_model = persistence_model_data_model.get_model(connection_info.contained_model_id)
        setattr(persistence_contained_model, connection_info.field_id, value)
        await persistence_connector.consume(persistence_model)

async def get_persistence_value(persistence_connector: Connector, connection_info: ConnectionInfo) -> Any:
    persistence_model = await persistence_connector.provide()
    if not connection_info.contained_model_id and not connection_info.field_id:
        return persistence_model
    elif not connection_info.field_id:
        persistence_model_data_model = DataModel.from_models(persistence_model)
        persistence_contained_model = persistence_model_data_model.get_model(connection_info.contained_model_id)
        return persistence_contained_model
    elif not connection_info.contained_model_id:
        return getattr(persistence_model, connection_info.field_id)
    else:
        persistence_model_data_model = DataModel.from_models(persistence_model)
        persistence_contained_model = persistence_model_data_model.get_model(connection_info.contained_model_id)
        return getattr(persistence_contained_model, connection_info.field_id)

def generate_persistence_connector_endpoint(connector_id: str, connector: Union[Consumer, Provider, Connector], connection_info: ConnectionInfo, model_type: Type[Any], persistence_registry: PersistenceConnectionRegistry) -> List[APIRouter]:
    """
    Generates endpoints for a workflow to execute the workflow.

    Args:
        workflow (Workflow): Workflow that contains the function to be executed by the workflow.

    Returns:
        APIRouter: FastAPI router with an endpoint to execute the workflow.
    """
    router = APIRouter(
        prefix=f"/{connector_id}",
        tags=["workflows"],
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
            persistence_connector = persistence_registry.get_connector_by_data_model_and_model_id(data_model_name=connection_info.data_model_name, model_id=connection_info.model_id)
            if value is None:
                # TODO: data model connection info is not yet possible
                value = await get_persistence_value(persistence_connector, connection_info)
            else:
                await update_persistence_with_value(persistence_connector, connection_info, value)
            await connector.consume(value)
            return {"message": f"Set for {connector_id} value {value}"}
        
    if isinstance(connector, Provider):
        @router.get("/value", response_model=model_type)
        async def get_value():
            return_value = await connector.provide()
            persistence_connector = persistence_registry.get_connector_by_data_model_and_model_id(data_model_name=connection_info.data_model_name, model_id=connection_info.model_id)
            await update_persistence_with_value(persistence_connector, connection_info, return_value)
            return return_value
            
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
        prefix=f"/{connector_id}",
        tags=["workflows"],
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
            await connector.consume(value)
            return {"message": f"Set value for {connector_id}"}
        
    if isinstance(connector, Provider):
        @router.get("/value", response_model=model_type)
        async def get_value():
            return await connector.provide()

    return router
