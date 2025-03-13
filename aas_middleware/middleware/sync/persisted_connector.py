from typing import Any, Optional, TypeVar, List, Dict

from aas_middleware.connect.connectors.connector import Connector, Provider, Consumer
from aas_middleware.middleware.sync.synced_connector import (
    SyncDirection,
    SyncRole,
)
from aas_middleware.middleware.sync.connector_sync_manager import connector_sync_manager
from aas_middleware.middleware.sync.synchronization import update_connector_with_value

T = TypeVar("T")


class PersistedConnector:
    """
    A wrapper around a persistence connector that notifies synced connectors when data changes.
    This enables bidirectional synchronization - not only from external connectors to persistence
    but also from persistence to external connectors.
    """

    def __init__(self, connector: Connector, connector_id: str):
        self.connector = connector
        self.connector_id = connector_id

    async def connect(self) -> None:
        """Connects the underlying connector."""
        await self.connector.connect()

    async def disconnect(self) -> None:
        """Disconnects the underlying connector."""
        await self.connector.disconnect()

    async def _notify_synced_connectors(self, value: Any) -> None:
        """
        Notifies all synced connectors connected to this persistence connector.

        Args:
            value: The new value from persistence
        """
        synced_connectors = (
            connector_sync_manager.get_synced_connectors_for_persistence(
                self.connector_id
            )
        )

        for synced_connector in synced_connectors:
            # Skip ground truth connectors - they shouldn't receive updates from persistence
            if synced_connector.sync_role == SyncRole.GROUND_TRUTH:
                continue

            # Skip connectors that don't sync from persistence
            if synced_connector.sync_direction == SyncDirection.TO_PERSISTENCE:
                continue

            # Transform the data for the external connector
            transformed_value = synced_connector._transform_from_persistence(value)

            # Update the connector
            if isinstance(synced_connector.connector, Consumer):
                connection_info = synced_connector.connection_info
                await update_connector_with_value(synced_connector, connection_info, transformed_value)

    async def _sync_ground_truth_connecters(self) -> None:
        """
        Syncs the ground truth connectors with the persistence connector to ensure they have the latest data.
        This is useful when the persistence connector is updated and we want to ensure that the ground truth connectors are in sync.
        """
        synced_connectors = (
            connector_sync_manager.get_synced_connectors_for_persistence(
                self.connector_id
            )
        )

        for synced_connector in synced_connectors:
            # Skip connectors that are not ground truth
            if synced_connector.sync_role != SyncRole.GROUND_TRUTH:
                continue
            # provide wiith the ground truth role to updatre automatically the persistence connector value
            if isinstance(synced_connector.connector, Provider):
                await synced_connector.provide()

    async def provide(self) -> T:
        """
        Provides data from the persistence connector.
        """
        if not isinstance(self.connector, Provider):
            raise TypeError("Underlying connector does not implement Provider protocol")
        await self._sync_ground_truth_connecters()
        value = await self.connector.provide()
        return value

    async def provide_persistence_value(self) -> T:
        """
        Provides data from the persistence connector.
        """
        if not isinstance(self.connector, Provider):
            raise TypeError("Underlying connector does not implement Provider protocol")
        value = await self.connector.provide()
        return value

    async def consume(self, body: T) -> None:
        """
        Consumes data and notifies connected synced connectors.
        """
        if not isinstance(self.connector, Consumer):
            raise TypeError("Underlying connector does not implement Consumer protocol")

        await self.connector.consume(body)
        await self._notify_synced_connectors(body)


def wrap_persistence_connector(
    persistence_connector: Connector, connector_id: str
) -> PersistedConnector:
    """
    Wraps a persistence connector with a PersistedConnector to enable bidirectional synchronization.

    Args:
        persistence_connector: The persistence connector to wrap
        connector_id: ID of the persistence connector

    Returns:
        A PersistedConnector that wraps the persistence connector
    """
    return PersistedConnector(persistence_connector, connector_id)
