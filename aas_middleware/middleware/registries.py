import typing

import logging

logger = logging.getLogger(__name__)

from pydantic import BaseModel, ConfigDict

from aas_middleware.connect.connectors.connector import Connector, Consumer, Provider
from aas_middleware.connect.connectors.model_connector import ModelConnector
from aas_middleware.connect.workflows.worfklow_description import WorkflowDescription
from aas_middleware.connect.workflows.workflow import Workflow
from aas_middleware.middleware.persistence_factory import PersistenceFactory
from aas_middleware.model.core import Identifiable


class ConnectionInfo(BaseModel):
    """
    Class that contains the information of a connection of a provider and a consumer to the persistence layer.
    """
    data_model_name: str
    model_id: typing.Optional[str] = None
    contained_model_id: typing.Optional[str] = None
    field_id: typing.Optional[str] = None

    model_config = ConfigDict(frozen=True, protected_namespaces=())

    @property
    def connection_type(self) -> typing.Literal["data_model", "model", "contained_model", "field"]:
        if self.model_id:
            if self.contained_model_id:
                if self.field_id:
                    return "field"
                return "contained_model"
            return "model"
        return "data_model"
    

class ConnectionRegistry:
    """
    Class that manages the connections of the middleware.
    """

    def __init__(self):
        self.connectors: typing.Dict[str, Connector] = {}
        self.connection_types: typing.Dict[str, typing.Type[Connector]] = {}
        self.connections: typing.Dict[ConnectionInfo, typing.List[str]] = {}


    def get_connector_id(self, connector: Connector) -> str:
        """
        Function to get a connector id from the connection manager.

        Args:
            connector (Connector): The connector of the connection.

        Returns:
            str: The id of the connector.

        Raises:
            KeyError: If the connector is not in the connection manager.
        """
        for connector_id, connector_ in self.connectors.items():
            if connector == connector_:
                return connector_id
        raise KeyError(f"Connector {connector} is not in the connection manager.")


    def get_connector(self, connector_id: str) -> Connector:
        """
        Function to get a connector from the connection manager.

        Args:
            connector_id (str): The id of the connector.

        Returns:
            Connector: The connector of the connection.

        Raises:
            KeyError: If the connector id is not in the connection manager.
        """
        return self.connectors[connector_id]


    def add_connector(self, connector_id: str, connector: Connector, connection_type: typing.Type[Connector]):
        """
        Function to add a connector to the connection manager.

        Args:
            connector_id (str): The name of the connector.
            connector (Connector): The connector to be added.
            connection_type (typing.Type[Connector]): The type of the connector.
        """
        self.connectors[connector_id] = connector
        self.connection_types[connector_id] = connection_type

    def add_connection(self, connector_id: str, connection_info: ConnectionInfo, connector: Connector, type_connection_info: typing.Type[typing.Any]):
        """
        Function to add a connection to the connection manager.

        Args:
            connector_id (str): The id of the connector.
            connection_info (ConnectionInfo): The connection info of the connection.
            connector (Connector): The connector of the connection.
            type_connection_info (typing.Type[typing.Any]): The type of the connection info of the connection.
        """
        if not connection_info in self.connections:
            self.connections[connection_info] = []
        self.connections[connection_info].append(connector_id)
        self.add_connector(connector_id, connector, type_connection_info)

    def get_connections(self, connection_info: ConnectionInfo) -> typing.List[typing.Tuple[Connector, typing.Type[typing.Any]]]:
        """
        Function to get a connection from the connection manager.

        Args:
            connection_info (ConnectionInfo): The connection info of the connection.

        Returns:
            Connector: The connector of the connection.
        """
        connector_ids = self.connections[connection_info]
        connections = []
        for connector_id in connector_ids:
            connections.append((self.get_connector(connector_id), self.connection_types[connector_id]))
        return connections
    
    def get_data_model_connection_info(self, data_model_name: str) -> typing.List[ConnectionInfo]:
        """
        Function to get the connection info of a data model.

        Args:
            data_model_name (str): The name of the data model.

        Returns:
            typing.Set[ConnectionInfo]: The connection info of the data model.
        """
        connection_infos = []
        for connection_info in self.connections:
            if not connection_info.data_model_name == data_model_name:
                continue
            connection_infos.append(connection_info)
        return connection_infos
    
    def get_model_connection_info(self, model_id: str) -> typing.List[ConnectionInfo]:
        """
        Function to get the connection info of a model.

        Args:
            model_id (str): The id of the model.

        Returns:
            typing.Set[ConnectionInfo]: The connection info of the model.
        """
        connection_infos = []
        for connection_info in self.connections:
            if not connection_info.model_id == model_id:
                continue
            connection_infos.append(connection_info)
        return connection_infos
    
    def get_field_connection_info(self, field_id: str) -> typing.List[ConnectionInfo]:
        """
        Function to get the connection info of a field.

        Args:
            field_id (str): The id of the field.

        Returns:
            typing.Set[ConnectionInfo]: The connection info of the field.
        """
        connection_infos = []
        for connection_info in self.connections:
            if not connection_info.field_id == field_id:
                continue
            connection_infos.append(connection_info)
        return connection_infos
    
    def get_type_connection_info(self, type_name: str) -> typing.List[ConnectionInfo]:
        """
        Function to get the connection info of a type.

        Args:
            type_name (str): The name of the type.

        Returns:
            typing.Set[ConnectionInfo]: The connection info of the type.
        """
        connection_infos = []
        for connection_info, connections in self.connections.items():
            for connection in connections:
                if not connection[1].__name__ == type_name:
                    continue
                connection_infos.append(connection_info)
        return connection_infos
    

class PersistenceConnectionRegistry(ConnectionRegistry):
    """
    Class that manages the connections of the middleware.
    """

    def __init__(self):
        super().__init__()
        self.connectors: typing.Dict[str, Connector] = {}
        self.connection_types: typing.Dict[str, typing.Type[Connector]] = {}
        self.connections: typing.Dict[ConnectionInfo, str] = {}
        self.persistence_factories: typing.Dict[ConnectionInfo, typing.List[typing.Tuple[PersistenceFactory, typing.Type[typing.Any]]]] = {}


    def get_connector_by_data_model_and_model_id(self, data_model_name: str, model_id: str) -> Connector:
        """
        Function to get a connector from the connection manager.

        Args:
            data_model_name (str): The name of the data model.
            model_id (str): The id of the model.

        Returns:
            Connector: The connector of the connection.

        Raises:
            KeyError: If the model id is not in the connection manager.
        """
        connector_id = data_model_name + model_id + "_persistence"
        return self.get_connector(connector_id)

    def add_persistence_factory(self, connection_info: ConnectionInfo, model_type: typing.Type[typing.Any], persistence_factory: PersistenceFactory):
        """
        Function to add a persistence factory to the connection manager.

        Args:
            connection_info (ConnectionInfo): The connection info of the connection.
            persistence_factory (PersistenceFactory): The persistence factory of the connection.
        """
        if not connection_info in self.persistence_factories:
            self.persistence_factories[connection_info] = []
        self.persistence_factories[connection_info].append((model_type, persistence_factory))

    def get_default_persistence_factory(self, connection_info: ConnectionInfo, persisted_model_type: typing.Type[typing.Any]) -> PersistenceFactory:
        """
        Function to get the default persistence factory of a connection.

        Args:
            connection_info (ConnectionInfo): The connection info of the connection.

        Returns:
            PersistenceFactory: The default persistence factory of the connection.
        """
        data_model_connection_info = ConnectionInfo(data_model_name=connection_info.data_model_name)
        if not data_model_connection_info in self.persistence_factories:
            logger.warning(f"No persistence factory found for {data_model_connection_info}. Using default persistence factory.")
            return PersistenceFactory(ModelConnector)
        for model_type, persistence_factory in self.persistence_factories[data_model_connection_info]:
            if issubclass(persisted_model_type, model_type):
                return persistence_factory
        logger.warning(f"No persistence factory found for {data_model_connection_info} and model type {persisted_model_type.__name__}. Using default persistence factory.")
        return PersistenceFactory(ModelConnector)

    def add_to_persistence(self, connection_info: ConnectionInfo, model: Identifiable, persistence_factory: typing.Optional[PersistenceFactory]):
        """
        Function to add a persistent connection to the connection manager.

        Args:
            connection_info (ConnectionInfo): The connection info of the connection.
        """
        if not persistence_factory:
            persistence_factory = self.get_default_persistence_factory(connection_info, type(model))
        connector = persistence_factory.create(model)
        self.add_connection(connection_info, connector, type(model))

    def add_connection(self, connection_info: ConnectionInfo, connector: Connector, type_connection_info: typing.Type[typing.Any]):
        """
        Function to add a connection to the connection manager.

        Args:
            connection_info (ConnectionInfo): The connection info of the connection.
            connector (Connector): The connector of the connection.
        """
        connector_id = connection_info.data_model_name + connection_info.model_id + "_persistence"
        self.add_connector(connector_id, connector, type_connection_info)
        self.connections[connection_info] = connector_id


    def remove_connection(self, connection_info: ConnectionInfo):
        """
        Function to remove a connection from the connection manager.

        Args:
            connection_info (ConnectionInfo): The connection info of the connection.
        """
        del self.connections[connection_info]
        # TODO: also delete connector and connection type

    def get_connection(self, connection_info: ConnectionInfo) -> Connector:
        """
        Function to get a connection from the connection manager.

        Args:
            connection_info (ConnectionInfo): The connection info of the connection.

        Returns:
            Connector: The connector of the connection.

        Raises:
            KeyError: If the connection info is not in the connection manager.
        """
        if connection_info in self.connections:
            return self.get_connector(self.connections[connection_info])
        raise KeyError(f"Data model Connection info {connection_info} is not in the connection manager.")

    def get_type_connection_info(self, type_name: str) -> typing.List[ConnectionInfo]:
        """
        Function to get the connection info of a type.

        Args:
            type_name (str): The name of the type.

        Returns:
            typing.Set[ConnectionInfo]: The connection info of the type.
        """
        connection_infos = []
        for connection_info, connector_id in self.connections.items():
            model_type = self.connection_types[connector_id]
            if not model_type.__name__ == type_name:
                continue
            connection_infos.append(connection_info)
        return connection_infos


class WorkflowRegistry:
    """
    Class that manages the workflows of the registry.
    """

    def __init__(self):
        self.workflows: typing.Dict[str, Workflow] = {}

        self.workflow_providers: typing.Dict[str, typing.List[typing.Tuple[ConnectionInfo, Provider]]] = {}
        self.workflow_consumers: typing.Dict[str, typing.List[typing.Tuple[ConnectionInfo, Consumer]]] = {}

    def add_workflow(self, workflow: Workflow):
        """
        Function to add a workflow to the registry.

        Args:
            workflow (Workflow): The workflow to be added.
        """
        self.workflows[workflow.get_name()] = workflow

    # def add_provider_to_workflow(self, workflow_name: str, connection_info: ConnectionInfo, provider: Provider):
    #     """
    #     Function to add a provider to a workflow.

    #     Args:
    #         workflow_name (str): The name of the workflow.
    #         connection_info (ConnectionInfo): The connection info of the provider.
    #         provider (Provider): The provider to be added.
    #     """
    #     if not workflow_name in self.workflow_providers:
    #         self.workflow_providers[workflow_name] = []
    #     self.workflow_providers[workflow_name].append((connection_info, provider))

    # def add_consumer_to_workflow(self, workflow_name: str, connection_info: ConnectionInfo, connector: Connector):
    #     """
    #     Function to add a consumer to a workflow.

    #     Args:
    #         workflow_name (str): The name of the workflow.
    #         connection_info (ConnectionInfo): The connection info of the consumer.
    #         connector (Connector): The connector to be added.
    #     """
    #     if not workflow_name in self.workflow_consumers:
    #         self.workflow_consumers[workflow_name] = []
    #     self.workflow_consumers[workflow_name].append((connection_info, connector))

    def get_workflows(self) -> typing.List[Workflow]:
        """
        Function to get the workflows in the registry.

        Returns:
            typing.List[Workflow]: The workflows in the registry.
        """
        return list(self.workflows.values())

    def get_workflow(self, workflow_name: str) -> Workflow:
        """
        Function to get a workflow from the registry.

        Args:
            workflow_name (str): The name of the workflow.

        Returns:
            Workflow: The workflow from the registry.

        Raises:
            KeyError: If the workflow is not in the registry.
        """
        return self.workflows[workflow_name]
    
    # def get_providers(self, workflow_name: str) -> typing.List[typing.Tuple[ConnectionInfo, Provider]]:
    #     """
    #     Function to get the providers of a workflow.

    #     Args:
    #         workflow_name (str): The name of the workflow.

    #     Returns:
    #         typing.List[typing.Tuple[ConnectionInfo, Provider]]: The providers of the workflow.
    #     """
    #     return self.workflow_providers[workflow_name]
    
    # def get_consumers(self, workflow_name: str) -> typing.List[typing.Tuple[ConnectionInfo, Connector]]:
    #     """
    #     Function to get the consumers of a workflow.

    #     Args:
    #         workflow_name (str): The name of the workflow.

    #     Returns:
    #         typing.List[typing.Tuple[ConnectionInfo, Connector]]: The consumers of the workflow.
    #     """
    #     return self.workflow_consumers[workflow_name]
    
    def get_workflow_names(self) -> typing.List[str]:
        """
        Function to get the names of the workflows in the registry.

        Returns:
            typing.List[str]: The names of the workflows in the registry.
        """
        return list(self.workflows.keys())
    
    def get_workflow_descriptions(self) -> typing.List[WorkflowDescription]:
        """
        Function to get the descriptions of the workflows in the registry.

        Returns:
            typing.List[WorkflowDescription]: The descriptions of the workflows in the registry.
        """
        return [workflow.get_description() for workflow in self.workflows.values()]
    
