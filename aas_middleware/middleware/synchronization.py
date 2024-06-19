from functools import wraps
from typing import Any, Union

from aas_middleware.connect.connectors.connector import Connector, Consumer, Provider
from aas_middleware.middleware.registries import ConnectionInfo, PersistenceConnectionRegistry
from aas_middleware.model.data_model import DataModel
from aas_middleware.model.util import get_value_attributes


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


def synchronize_connector_with_persistence(connector: Union[Consumer, Provider], connection_info: ConnectionInfo, persistence_registry: PersistenceConnectionRegistry):
    """
    Synchronizes a connector with the persistence layer.

    Args:
        connector (Union[Consumer, Provider]): The connector to synchronize.
        connection_info (ConnectionInfo): The connection info for the persistence layer.
        persistence_registry (PersistenceConnectionRegistry): The registry for the persistence connectors.    
    """
    if isinstance(connector, Consumer):
        original_consume = connector.consume

        @wraps(connector.consume)
        async def wrapped_consume(body: Any):
            persistence_connector = persistence_registry.get_connector_by_data_model_and_model_id(data_model_name=connection_info.data_model_name, model_id=connection_info.model_id)
            if body is None:
                # TODO: data model connection info is not yet possible
                body = await get_persistence_value(persistence_connector, connection_info)
            else:
                await update_persistence_with_value(persistence_connector, connection_info, body)
            await original_consume(body)

        connector.consume = wrapped_consume

    if isinstance(connector, Provider):
        original_provide = connector.provide

        @wraps(connector.provide)
        async def wrapped_provide() -> Any:
            persistence_connector = persistence_registry.get_connector_by_data_model_and_model_id(data_model_name=connection_info.data_model_name, model_id=connection_info.model_id)
            body = await original_provide()
            await update_persistence_with_value(persistence_connector, connection_info, body)
            return body

        connector.provide = wrapped_provide