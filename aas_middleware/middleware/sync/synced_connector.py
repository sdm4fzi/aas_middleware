from __future__ import annotations

from enum import Enum, auto
from typing import (
    Any,
    Optional,
    Union,
    TypeVar,
    Generic,
    AsyncGenerator,
    Protocol,
    runtime_checkable,
)
import typing

from aas_middleware.connect.connectors.connector import Connector, Consumer, Provider
from aas_middleware.connect.connectors.async_connector import AsyncConnector, Receiver

from aas_middleware.middleware.sync.connector_sync_manager import connector_sync_manager
from aas_middleware.model.formatting.formatter import Formatter
from aas_middleware.model.mapping.mapper import Mapper

from aas_middleware.middleware.sync.synchronization import (
    get_persistence_value,
    update_persistence_with_value,
    adjust_body_for_persistence_schema,
    adjust_body_for_external_schema,
)

if typing.TYPE_CHECKING:
    from aas_middleware.middleware.registries import (
        ConnectionInfo,
        PersistenceConnectionRegistry,
    )

class SyncRole(Enum):
    """Defines the role of a connector in the synchronization process."""

    GROUND_TRUTH = auto()  # This connector's data always overrides persistence
    READ_ONLY = auto()  # This connector only reads from persistence
    READ_WRITE = auto()  # This connector reads from and writes to persistence
    WRITE_ONLY = auto()  # This connector only writes to persistence


class SyncDirection(Enum):
    """Defines the direction of synchronization."""

    TO_PERSISTENCE = auto()  # Sync data from connector to persistence
    FROM_PERSISTENCE = auto()  # Sync data from persistence to connector
    BIDIRECTIONAL = auto()  # Sync data in both directions


T = TypeVar("T")


@runtime_checkable
class SyncedProtocol(Protocol):
    """Protocol for objects that expose their sync configuration."""

    @property
    def sync_role(self) -> SyncRole:
        """Returns the sync role of this connector."""
        ...

    @property
    def sync_direction(self) -> SyncDirection:
        """Returns the sync direction of this connector."""
        ...

    @property
    def connection_info(self) -> ConnectionInfo:
        """Returns the connection info for this connector."""
        ...


class SyncedConnector(Generic[T]):
    """
    A wrapper around a connector that adds synchronization capabilities.
    This class maintains the original connector's interface while adding
    transparent synchronization with the persistence layer.
    """

    def __init__(
        self,
        connector: Union[Connector, AsyncConnector],
        connection_info: ConnectionInfo,
        persistence_registry: PersistenceConnectionRegistry,
        role: SyncRole = SyncRole.READ_WRITE,
        direction: SyncDirection = SyncDirection.BIDIRECTIONAL,
        persistence_mapper: Optional[Mapper] = None,
        external_mapper: Optional[Mapper] = None,
        formatter: Optional[Formatter] = None,
        priority: int = 1,
    ):
        self.connector = connector
        self._connection_info = connection_info
        self.persistence_registry = persistence_registry
        self._sync_role = role
        self._sync_direction = direction
        self.persistence_mapper = persistence_mapper
        self.external_mapper = external_mapper
        self.formatter = formatter
        self.priority = priority

    @property
    def sync_role(self) -> SyncRole:
        """Returns the sync role of this connector."""
        return self._sync_role

    @property
    def sync_direction(self) -> SyncDirection:
        """Returns the sync direction of this connector."""
        return self._sync_direction

    @property
    def connection_info(self) -> ConnectionInfo:
        """Returns the connection info for this connector."""
        return self._connection_info

    async def connect(self) -> None:
        """Connects the underlying connector."""
        await self.connector.connect()

    async def disconnect(self) -> None:
        """Disconnects the underlying connector."""
        await self.connector.disconnect()

    async def _get_persistence_connector(self) -> Connector:
        """Gets the persistence connector for the connection info."""
        return self.persistence_registry.get_connector_by_data_model_and_model_id(
            data_model_name=self.connection_info.data_model_name,
            model_id=self.connection_info.model_id,
        )

    async def _get_persistence_value(self) -> Any:
        """Gets the value from the persistence connector."""
        persistence_connector = await self._get_persistence_connector()
        return await get_persistence_value(persistence_connector, self.connection_info)

    async def _update_persistence_value(self, value: Any) -> None:
        """Updates the value in the persistence connector."""
        persistence_connector = await self._get_persistence_connector()
        await update_persistence_with_value(
            persistence_connector, self.connection_info, value
        )

    def _transform_for_persistence(self, value: Any) -> Any:
        """Transforms the value for the persistence layer."""
        return adjust_body_for_persistence_schema(
            value, external_mapper=self.external_mapper, formatter=self.formatter
        )

    def _transform_from_persistence(self, value: Any) -> Any:
        """Transforms the value from the persistence layer."""
        return adjust_body_for_external_schema(
            value, persistence_mapper=self.persistence_mapper, formatter=self.formatter
        )

    async def provide(self) -> T:
        """
        Provides data from the connector with synchronization.
        If the connector is not ground truth, this may return data from persistence.
        """
        if not isinstance(self.connector, Provider):
            raise TypeError("Underlying connector does not implement Provider protocol")

        # For ground truth connectors, always use their data and update persistence
        if self.sync_role == SyncRole.GROUND_TRUTH:
            connector_data = await self.connector.provide()
            if self.sync_direction in (
                SyncDirection.TO_PERSISTENCE,
                SyncDirection.BIDIRECTIONAL,
            ):
                persistence_data = self._transform_for_persistence(connector_data)
                await self._update_persistence_value(persistence_data)
            return connector_data

        # For non-ground truth connectors that read from persistence
        if self.sync_direction in (
            SyncDirection.FROM_PERSISTENCE,
            SyncDirection.BIDIRECTIONAL,
        ):
            try:
                persistence_data = await self._get_persistence_value()
                transformed_data = self._transform_from_persistence(persistence_data)
                # TODO: this case should consider if persistence and connector data are the same -> resolve then
                return transformed_data
            except Exception as e:
                # Fall back to connector data if persistence fails
                pass

        connector_data = await self.connector.provide()

        # Update persistence if we're supposed to write to it
        if self.sync_direction in (
            SyncDirection.TO_PERSISTENCE,
            SyncDirection.BIDIRECTIONAL,
        ):
            persistence_data = self._transform_for_persistence(connector_data)
            await self._update_persistence_value(persistence_data)

        return connector_data
    
    async def consume_unsynced(self, body: T) -> None:
        """
        Consumes data without synchronization.
        """
        if not isinstance(self.connector, Consumer):
            raise TypeError("Underlying connector does not implement Consumer protocol")

        await self.connector.consume(body)

    async def consume(self, body: T) -> None:
        """
        Consumes data with synchronization.
        Updates the persistence layer based on configuration.
        """
        if not isinstance(self.connector, Consumer):
            raise TypeError("Underlying connector does not implement Consumer protocol")

        # Skip persistence updates for read-only connectors
        if self.sync_role == SyncRole.READ_ONLY:
            # Still pass data to the underlying connector
            await self.connector.consume(body)
            return

        # If no data provided, try to get from persistence first
        if body is None and self.sync_direction in (
            SyncDirection.FROM_PERSISTENCE,
            SyncDirection.BIDIRECTIONAL,
        ):
            try:
                persistence_data = await self._get_persistence_value()
                body = self._transform_from_persistence(persistence_data)
                # TODO: this case should consider if persistence and connector data are the same -> resolve then
            except Exception:
                # Continue with None if this fails
                pass

        # Update persistence if configured to do so
        if body is not None and self.sync_direction in (
            SyncDirection.TO_PERSISTENCE,
            SyncDirection.BIDIRECTIONAL,
        ):
            persistence_data = self._transform_for_persistence(body)
            await self._update_persistence_value(persistence_data)

        # Always pass the data to the underlying connector
        await self.connector.consume(body)

    async def receive(self) -> AsyncGenerator[T, None]:
        """
        Implements the Receiver protocol with synchronization.
        """
        if not isinstance(self.connector, Receiver):
            raise TypeError("Underlying connector does not implement Receiver protocol")

        async for item in self.connector.receive():
            # For ground truth or write-enabled connectors, update persistence
            if self.sync_role in (
                SyncRole.GROUND_TRUTH,
                SyncRole.READ_WRITE,
                SyncRole.WRITE_ONLY,
            ) and self.sync_direction in (
                SyncDirection.TO_PERSISTENCE,
                SyncDirection.BIDIRECTIONAL,
            ):
                persistence_data = self._transform_for_persistence(item)
                await self._update_persistence_value(persistence_data)

            yield item


def create_synced_connector(
    connector: Union[Connector, AsyncConnector],
    connection_info: ConnectionInfo,
    persistence_registry: PersistenceConnectionRegistry,
    sync_role: SyncRole = SyncRole.READ_WRITE,
    sync_direction: SyncDirection = SyncDirection.BIDIRECTIONAL,
    persistence_mapper: typing.Optional[Mapper] = None,
    external_mapper: typing.Optional[Mapper] = None,
    formatter: typing.Optional[Formatter] = None,
    priority: int = 1,
    connector_id: str = None,
) -> SyncedConnector:
    """
    Creates a SyncedConnector that wraps the original connector with synchronization capabilities.
    Also registers the sync relationship with the SyncManager.

    Args:
        connector_id: ID of the connector (for registration)
        connector: The connector to sync with persistence
        connection_info: Information about the connection
        persistence_registry: Registry containing persistence connectors
        sync_role: The role of this connector in synchronization
        sync_direction: Direction of data flow for synchronization
        persistence_mapper: Mapper for transforming persistence data
        external_mapper: Mapper for transforming external data
        formatter: Formatter for serializing/deserializing data
        priority: Priority level for conflict resolution (higher wins)

    Returns:
        A SyncedConnector instance that wraps the original connector
    """
    synced_connector = SyncedConnector(
        connector=connector,
        connection_info=connection_info,
        persistence_registry=persistence_registry,
        role=sync_role,
        direction=sync_direction,
        persistence_mapper=persistence_mapper,
        external_mapper=external_mapper,
        formatter=formatter,
        priority=priority,
    )

    persistence_connector = (
        persistence_registry.get_connector_by_data_model_and_model_id(
            data_model_name=connection_info.data_model_name,
            model_id=connection_info.model_id,
        )
    )
    persistence_connector_id = persistence_registry.get_connector_id(
        persistence_connector
    )
    connector_sync_manager.register_sync_relationship(
        synced_connector=synced_connector,
        connector_id=connector_id,
        persistence_connector_id=persistence_connector_id,
    )

    return synced_connector


def synchronize_connector_with_persistence(
    connector_id: str,
    connector: Union[Consumer, Provider],
    connection_info: ConnectionInfo,
    persistence_registry: PersistenceConnectionRegistry,
    sync_role: SyncRole = SyncRole.READ_WRITE,
    sync_direction: SyncDirection = SyncDirection.BIDIRECTIONAL,
    persistence_mapper: typing.Optional[Mapper] = None,
    external_mapper: typing.Optional[Mapper] = None,
    formatter: typing.Optional[Formatter] = None,
) -> SyncedConnector:
    """
    Creates a SyncedConnector and returns it. This is the recommended
    approach for synchronizing connectors with persistence.

    Args:
        connector_id: ID of the connector (for registration)
        connector: The connector to sync with persistence
        connection_info: Information about the connection
        persistence_registry: Registry containing persistence connectors
        sync_role: The role of this connector in synchronization
        sync_direction: Direction of data flow for synchronization
        persistence_mapper: Mapper for transforming persistence data
        external_mapper: Mapper for transforming external data
        formatter: Formatter for serializing/deserializing data

    Returns:
        A SyncedConnector instance
    """
    return create_synced_connector(
        connector=connector,
        connection_info=connection_info,
        persistence_registry=persistence_registry,
        sync_role=sync_role,
        sync_direction=sync_direction,
        persistence_mapper=persistence_mapper,
        external_mapper=external_mapper,
        formatter=formatter,
        connector_id=connector_id,
    )
