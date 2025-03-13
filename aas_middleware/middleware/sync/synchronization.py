from __future__ import annotations

from functools import wraps
from typing import Any, Union
import typing

from aas_middleware.connect.connectors.connector import Connector, Consumer, Provider
from aas_middleware.connect.connectors.async_connector import AsyncConnector
from aas_middleware.connect.workflows.workflow import Workflow

from aas_middleware.model.data_model import DataModel
from aas_middleware.model.formatting.formatter import Formatter
from aas_middleware.model.mapping.mapper import Mapper
from aas_middleware.model.util import get_value_attributes


if typing.TYPE_CHECKING:
    from aas_middleware.middleware.registries import (
        ConnectionInfo,
        PersistenceConnectionRegistry,
    )
    from aas_middleware.middleware.sync.persisted_connector import PersistedConnector
    from aas_middleware.middleware.sync.synced_connector import (
        SyncedConnector)

async def update_persistence_with_value(
    persistence_connector: PersistedConnector, connection_info: ConnectionInfo, value: Any
):
    if not connection_info.contained_model_id and not connection_info.field_id:
        # TODO: handle case when id of model changes...
        # TODO: also handle case when new models are added in the data model
        await persistence_connector.consume(value)
    elif not connection_info.field_id:
        persistence_model = await persistence_connector.provide_persistence_value()
        persistence_model_data_model = DataModel.from_models(persistence_model)
        # TODO: make sure when id changes the connection info changes as well
        persistence_contained_model = persistence_model_data_model.get_model(
            connection_info.contained_model_id
        )
        referencing_models = persistence_model_data_model.get_referencing_models(
            persistence_contained_model
        )
        for referencing_model in referencing_models:
            for attribute_name, attribute_value in get_value_attributes(
                referencing_model
            ).items():
                if attribute_value == persistence_contained_model:
                    setattr(referencing_model, attribute_name, value)
        await persistence_connector.consume(persistence_model)
    elif not connection_info.contained_model_id:
        persistence_model = await persistence_connector.provide_persistence_value()
        setattr(persistence_model, connection_info.field_id, value)
        await persistence_connector.consume(persistence_model)
    else:
        persistence_model = await persistence_connector.provide_persistence_value()
        persistence_model_data_model = DataModel.from_models(persistence_model)
        persistence_contained_model = persistence_model_data_model.get_model(
            connection_info.contained_model_id
        )
        setattr(persistence_contained_model, connection_info.field_id, value)
        await persistence_connector.consume(persistence_model)


async def update_connector_with_value(
    connector: Connector, connection_info: ConnectionInfo, persistence_model: Any
) -> None:
    """
    Updates the connector with the value.

    Args:
        connector (Connector): The connector to update.
        connection_info (ConnectionInfo): The connection info for the connector.
        value (Any): The value to update the connector with.
    """
    if not connection_info.contained_model_id and not connection_info.field_id:
        await connector.consume_unsynced(persistence_model)
    elif not connection_info.field_id:
        persistence_model_data_model = DataModel.from_models(persistence_model)
        persistence_contained_model = persistence_model_data_model.get_model(
            connection_info.contained_model_id
        )
        await connector.consume_unsynced(persistence_contained_model)
    elif not connection_info.contained_model_id:
        await connector.consume_unsynced(
            getattr(persistence_model, connection_info.field_id)
        )
    else:
        persistence_model_data_model = DataModel.from_models(persistence_model)
        persistence_contained_model = persistence_model_data_model.get_model(
            connection_info.contained_model_id
        )
        await connector.consume_unsynced(
            getattr(persistence_contained_model, connection_info.field_id)
        )


async def get_persistence_value(
    persistence_connector: Connector, connection_info: ConnectionInfo
) -> Any:
    persistence_model = await persistence_connector.provide()
    if not connection_info.contained_model_id and not connection_info.field_id:
        return persistence_model
    elif not connection_info.field_id:
        persistence_model_data_model = DataModel.from_models(persistence_model)
        persistence_contained_model = persistence_model_data_model.get_model(
            connection_info.contained_model_id
        )
        return persistence_contained_model
    elif not connection_info.contained_model_id:
        return getattr(persistence_model, connection_info.field_id)
    else:
        persistence_model_data_model = DataModel.from_models(persistence_model)
        persistence_contained_model = persistence_model_data_model.get_model(
            connection_info.contained_model_id
        )
        return getattr(persistence_contained_model, connection_info.field_id)


def adjust_body_for_persistence_schema(
    body: Any,
    external_mapper: typing.Optional[Mapper] = None,
    formatter: typing.Optional[Formatter] = None,
) -> Any:
    """
    Modifies the body for persistence.

    Args:
        body (Any): The body to modify.
        external_mapper (typing.Optional[Mapper], optional): The mapper that maps the body to the persistence model. Defaults to None.
        formatter (typing.Optional[Formatter], optional): The formatter that serializes the body. Defaults to None.

    Returns:
        Any: The modified body.
    """
    if formatter:
        body = formatter.deserialize(body)
    if external_mapper:
        body = external_mapper.map(body)
    return body


def adjust_body_for_external_schema(
    body: Any,
    persistence_mapper: typing.Optional[Mapper] = None,
    formatter: typing.Optional[Formatter] = None,
) -> Any:
    """
    Modifies the body for an external schema.

    Args:
        body (Any): The body to modify.
        persistence_mapper (typing.Optional[Mapper], optional): The mapper that maps the body to the external model. Defaults to None.
        formatter (typing.Optional[Formatter], optional): The formatter that serializes the body. Defaults to None.

    Returns:
        Any: The modified body.
    """
    if persistence_mapper:
        body = persistence_mapper.map(body)
    if formatter:
        body = formatter.serialize(body)
    return body


def synchronize_workflow_with_persistence_consumer(
    workflow: Workflow,
    connection_info: ConnectionInfo,
    persistence_registry: PersistenceConnectionRegistry,
    external_mapper: typing.Optional[Mapper] = None,
    formatter: typing.Optional[Formatter] = None,
):
    """
    Synchronizes a workflow with a persistence consumer.

    Args:
        workflow (Workflow): The workflow to synchronize.
        arg_name (str): The name of the argument in the workflow that is a consumer.
        connection_info (ConnectionInfo): The connection info for the persistence layer.
        persistence_registry (PersistenceConnectionRegistry): The registry for the persistence connectors.
    """
    original_execute = workflow.execute

    @wraps(workflow.execute)
    async def wrapped_execute(execute_body: Any):
        workflow_return = await original_execute(execute_body)
        persistence_connector = (
            persistence_registry.get_connector_by_data_model_and_model_id(
                data_model_name=connection_info.data_model_name,
                model_id=connection_info.model_id,
            )
        )
        persistence_body = adjust_body_for_persistence_schema(
            workflow_return, external_mapper, formatter
        )
        await update_persistence_with_value(
            persistence_connector, connection_info, persistence_body
        )
        return workflow_return

    workflow.execute = wrapped_execute


def synchronize_workflow_with_persistence_provider(
    workflow: Workflow,
    arg_name: str,
    connection_info: ConnectionInfo,
    persistence_registry: PersistenceConnectionRegistry,
    persistence_mapper: typing.Optional[Mapper] = None,
    external_mapper: typing.Optional[Mapper] = None,
    formatter: typing.Optional[Formatter] = None,
):
    """
    Synchronizes a workflow with a persistence provider.

    Args:
        workflow (Workflow): _description_
        arg_name (str): _description_
        connection_info (ConnectionInfo): _description_
        persistence_registry (PersistenceConnectionRegistry): _description_
        persistence_mapper (typing.Optional[Mapper], optional): _description_. Defaults to None.
        external_mapper (typing.Optional[Mapper], optional): _description_. Defaults
        formatter (typing.Optional[Formatter], optional): _description_. Defaults to None.
    """
    original_execute = workflow.execute

    @wraps(workflow.execute)
    async def wrapped_execute(execute_body: Any):
        persistence_connector = (
            persistence_registry.get_connector_by_data_model_and_model_id(
                data_model_name=connection_info.data_model_name,
                model_id=connection_info.model_id,
            )
        )

        if not execute_body:
            persistence_body = await get_persistence_value(
                persistence_connector, connection_info
            )
            execute_body = adjust_body_for_external_schema(
                persistence_body, persistence_mapper, formatter
            )
        else:
            persistence_body = adjust_body_for_persistence_schema(
                execute_body, external_mapper, formatter
            )
            await update_persistence_with_value(
                persistence_connector, connection_info, persistence_body
            )

        workflow_return = await original_execute(execute_body)
        return workflow_return

    workflow.execute = wrapped_execute
