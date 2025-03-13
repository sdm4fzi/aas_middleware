from __future__ import annotations

from typing import TYPE_CHECKING, Dict, List, Set, Any, Tuple, Optional, Union
from weakref import WeakValueDictionary


if TYPE_CHECKING:
    from aas_middleware.middleware.sync.synced_connector import (
        SyncedConnector,
        SyncRole,
        SyncDirection,
    )
    from aas_middleware.middleware.registries import ConnectionInfo


class ConnectorSyncManager:
    """
    Manages synchronization relationships between connectors and persistence.
    Used to track which synced connectors are connected to which persistence connectors.
    """

    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(ConnectorSyncManager, cls).__new__(cls)
            cls._instance._initialize()
        return cls._instance

    def _initialize(self):
        # Map persistence connectors to their synced connectors
        self.persistence_to_synced: Dict[str, List[SyncedConnector]] = {}

        # Map connection info to persistence connector IDs
        self.connection_to_persistence: Dict[ConnectionInfo, str] = {}

        # Store all synced connectors by connector_id
        self.synced_connectors: WeakValueDictionary = WeakValueDictionary()

    def register_sync_relationship(
        self,
        synced_connector: SyncedConnector,
        connector_id: str,
        persistence_connector_id: str,
    ):
        """
        Registers a synchronization relationship between a synced connector and a persistence connector.

        Args:
            synced_connector: The synced connector
            connector_id: ID of the external connector
            persistence_connector_id: ID of the persistence connector
        """
        if persistence_connector_id not in self.persistence_to_synced:
            self.persistence_to_synced[persistence_connector_id] = []

        self.persistence_to_synced[persistence_connector_id].append(synced_connector)
        self.connection_to_persistence[synced_connector.connection_info] = (
            persistence_connector_id
        )
        self.synced_connectors[connector_id] = synced_connector

    def get_synced_connectors_for_persistence(
        self, persistence_connector_id: str
    ) -> List[SyncedConnector]:
        """
        Gets all synced connectors associated with a persistence connector.

        Args:
            persistence_connector_id: ID of the persistence connector

        Returns:
            List of synced connectors associated with the persistence connector
        """
        return self.persistence_to_synced.get(persistence_connector_id, [])

    def get_persistence_id_for_connection(
        self, connection_info: ConnectionInfo
    ) -> Optional[str]:
        """
        Gets the persistence connector ID for a connection info.

        Args:
            connection_info: The connection info

        Returns:
            ID of the persistence connector or None if not found
        """
        return self.connection_to_persistence.get(connection_info)

    def get_synced_connector(self, connector_id: str) -> Optional[SyncedConnector]:
        """
        Gets a synced connector by its ID.

        Args:
            connector_id: ID of the connector

        Returns:
            The synced connector or None if not found
        """
        return self.synced_connectors.get(connector_id)

    def is_synced_connector(self, connector_id: str) -> bool:
        """
        Checks if a connector is synced.

        Args:
            connector_id: ID of the connector

        Returns:
            True if the connector is synced, False otherwise
        """
        return connector_id in self.synced_connectors


# Global instance
connector_sync_manager = ConnectorSyncManager()
