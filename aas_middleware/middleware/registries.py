import typing
from pydantic import BaseModel, ConfigDict

from aas_middleware.connect.connectors.connector import Connector, Provider
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
    field_id: typing.Optional[str] = None
    model_type : typing.Optional[typing.Type[typing.Any]] = None

    model_config = ConfigDict(frozen=True, protected_namespaces=())

    @property
    def connection_type(self) -> typing.Literal["data_model", "model", "field"]:
        if self.model_id:
            if self.field_id:
                return "field"
            return "model"
        return "data_model"
    
class ConnectionRegistry:
    """
    Class that manages the connections of the middleware.
    """

    def __init__(self):
        self.connections: typing.Dict[ConnectionInfo, typing.List[Connector]] = {}

        self.data_model_connection_infos: typing.Dict[str, typing.List[ConnectionInfo]] = {}
        self.model_connection_infos: typing.Dict[str, typing.List[ConnectionInfo]] = {}
        self.field_connection_infos: typing.Dict[str, typing.List[ConnectionInfo]] = {}
        self.type_connection_infos: typing.Dict[str, typing.List[ConnectionInfo]] = {}

    def add_connection(self, connection_info: ConnectionInfo, connector: Connector):
        """
        Function to add a connection to the connection manager.

        Args:
            connection_info (ConnectionInfo): The connection info of the connection.
            connector (Connector): The connector of the connection.
        """
        if not connection_info in self.connections:
            self.connections[connection_info] = []
        self.connections[connection_info].append(connector)
        if connection_info.connection_type == "data_model":
            if not connection_info.data_model_name in self.data_model_connection_infos:
                self.data_model_connection_infos[connection_info.data_model_name] = []
            self.data_model_connection_infos[connection_info.data_model_name].append(connection_info)
        elif connection_info.connection_type == "model":
            if not connection_info.model_id in self.model_connection_infos:
                self.model_connection_infos[connection_info.model_id] = []
            self.model_connection_infos[connection_info.model_id].append(connection_info)
        elif connection_info.connection_type == "field":
            if not connection_info.field_id in self.field_connection_infos:
                self.field_connection_infos[connection_info.field_id] = []
            self.field_connection_infos[connection_info.field_id].append(connection_info)

    def get_connections(self, connection_info: ConnectionInfo) -> typing.List[Connector]:
        """
        Function to get a connection from the connection manager.

        Args:
            connection_info (ConnectionInfo): The connection info of the connection.

        Returns:
            Connector: The connector of the connection.
        """
        return self.connections[connection_info]
    
    def get_data_model_connection_info(self, data_model_name: str) -> typing.List[ConnectionInfo]:
        """
        Function to get the connection info of a data model.

        Args:
            data_model_name (str): The name of the data model.

        Returns:
            typing.Set[ConnectionInfo]: The connection info of the data model.
        """
        return self.data_model_connection_infos[data_model_name]
    
    def get_model_connection_info(self, model_id: str) -> typing.List[ConnectionInfo]:
        """
        Function to get the connection info of a model.

        Args:
            model_id (str): The id of the model.

        Returns:
            typing.Set[ConnectionInfo]: The connection info of the model.
        """
        return self.model_connection_infos[model_id]
    
    def get_field_connection_info(self, field_id: str) -> typing.List[ConnectionInfo]:
        """
        Function to get the connection info of a field.

        Args:
            field_id (str): The id of the field.

        Returns:
            typing.Set[ConnectionInfo]: The connection info of the field.
        """
        return self.field_connection_infos[field_id]
    
    def get_type_connection_info(self, type_name: str) -> typing.List[ConnectionInfo]:
        """
        Function to get the connection info of a type.

        Args:
            type_name (str): The name of the type.

        Returns:
            typing.Set[ConnectionInfo]: The connection info of the type.
        """
        # FIXME: restructure that connection infos can be queried more easily and that this function is working...
        return self.type_connection_infos[type_name]
    

class PersistenceConnectionRegistry(ConnectionRegistry):
    """
    Class that manages the connections of the middleware.
    """

    def __init__(self):
        super().__init__()
        self.connections: typing.Dict[ConnectionInfo, Connector] = {}
        self.persistence_factories: typing.Dict[ConnectionInfo, PersistenceFactory] = {}

    def add_persistence_factory(self, connection_info: ConnectionInfo, persistence_factory: PersistenceFactory):
        """
        Function to add a persistence factory to the connection manager.

        Args:
            connection_info (ConnectionInfo): The connection info of the connection.
            persistence_factory (PersistenceFactory): The persistence factory of the connection.
        """
        self.persistence_factories[connection_info] = persistence_factory

    def get_default_persistence_factory(self, connection_info: ConnectionInfo) -> PersistenceFactory:
        """
        Function to get the default persistence factory of a connection.

        Args:
            connection_info (ConnectionInfo): The connection info of the connection.

        Returns:
            PersistenceFactory: The default persistence factory of the connection.
        """
        if connection_info in self.persistence_factories:
            return self.persistence_factories[connection_info]
        type_connection_info = ConnectionInfo(data_model_name=connection_info.data_model_name, model_type=connection_info.model_type)
        if type_connection_info in self.persistence_factories:
            return self.persistence_factories[type_connection_info]
        data_model_connection_info = ConnectionInfo(data_model_name=connection_info.data_model_name)
        if data_model_connection_info in self.persistence_factories:
            return self.persistence_factories[data_model_connection_info]
        return PersistenceFactory(ModelConnector)

    def add_to_persistence(self, connection_info: ConnectionInfo, model: Identifiable, persistence_factory: typing.Optional[PersistenceFactory]):
        """
        Function to add a persistent connection to the connection manager.

        Args:
            connection_info (ConnectionInfo): The connection info of the connection.
        """
        if not persistence_factory:
            persistence_factory = self.get_default_persistence_factory(connection_info)
        connector = persistence_factory.create(model)
        self.add_connection(connection_info, connector)

    def add_connection(self, connection_info: ConnectionInfo, connector: Connector):
        """
        Function to add a connection to the connection manager.

        Args:
            connection_info (ConnectionInfo): The connection info of the connection.
            connector (Connector): The connector of the connection.
        """
        self.connections[connection_info] = connector
        if connection_info.connection_type == "data_model":
            if not connection_info.data_model_name in self.data_model_connection_infos:
                self.data_model_connection_infos[connection_info.data_model_name] = []
            self.data_model_connection_infos[connection_info.data_model_name].append(connection_info)
        elif connection_info.connection_type == "model":
            if not connection_info.model_id in self.model_connection_infos:
                self.model_connection_infos[connection_info.model_id] = []
            self.model_connection_infos[connection_info.model_id].append(connection_info)  
        elif connection_info.connection_type == "field":
            if not connection_info.field_id in self.field_connection_infos:
                self.field_connection_infos[connection_info.field_id] = []
            self.field_connection_infos[connection_info.field_id].append(connection_info)

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
            return self.connections[connection_info]
        if connection_info.field_id:
            raise KeyError(f"Field Connection info {connection_info} is not in the connection manager.")
        if connection_info.model_id:
            model_connection_info = ConnectionInfo(data_model_name=connection_info.data_model_name, model_id=connection_info.model_id, model_type=connection_info.model_type)
            if model_connection_info in self.connections:
                return self.connections[model_connection_info]
            model_connection_info = ConnectionInfo(data_model_name=connection_info.data_model_name, model_id=connection_info.model_id)
            if model_connection_info in self.connections:
                return self.connections[model_connection_info]
            raise KeyError(f"Model Connection info {connection_info} is not in the connection manager.")
        data_model_connection_info = ConnectionInfo(data_model_name=connection_info.data_model_name)
        if data_model_connection_info in self.connections:
            return self.connections[data_model_connection_info]
        raise KeyError(f"Data model Connection info {connection_info} is not in the connection manager.")



class WorkflowRegistry:
    """
    Class that manages the workflows of the registry.
    """

    def __init__(self):
        self.workflows: typing.Dict[str, Workflow] = {}

        self.workflow_providers: typing.Dict[str, typing.List[typing.Tuple[ConnectionInfo, Provider]]] = {}
        self.workflow_consumers: typing.Dict[str, typing.List[typing.Tuple[ConnectionInfo, Connector]]] = {}

    def add_workflow(self, workflow: Workflow):
        """
        Function to add a workflow to the registry.

        Args:
            workflow (Workflow): The workflow to be added.
        """
        self.workflows[workflow.get_name()] = workflow

    def add_provider_to_workflow(self, workflow_name: str, connection_info: ConnectionInfo, provider: Provider):
        """
        Function to add a provider to a workflow.

        Args:
            workflow_name (str): The name of the workflow.
            connection_info (ConnectionInfo): The connection info of the provider.
            provider (Provider): The provider to be added.
        """
        if not workflow_name in self.workflow_providers:
            self.workflow_providers[workflow_name] = []
        self.workflow_providers[workflow_name].append((connection_info, provider))

    def add_consumer_to_workflow(self, workflow_name: str, connection_info: ConnectionInfo, connector: Connector):
        """
        Function to add a consumer to a workflow.

        Args:
            workflow_name (str): The name of the workflow.
            connection_info (ConnectionInfo): The connection info of the consumer.
            connector (Connector): The connector to be added.
        """
        if not workflow_name in self.workflow_consumers:
            self.workflow_consumers[workflow_name] = []
        self.workflow_consumers[workflow_name].append((connection_info, connector))

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
    
    def get_providers(self, workflow_name: str) -> typing.List[typing.Tuple[ConnectionInfo, Provider]]:
        """
        Function to get the providers of a workflow.

        Args:
            workflow_name (str): The name of the workflow.

        Returns:
            typing.List[typing.Tuple[ConnectionInfo, Provider]]: The providers of the workflow.
        """
        return self.workflow_providers[workflow_name]
    
    def get_consumers(self, workflow_name: str) -> typing.List[typing.Tuple[ConnectionInfo, Connector]]:
        """
        Function to get the consumers of a workflow.

        Args:
            workflow_name (str): The name of the workflow.

        Returns:
            typing.List[typing.Tuple[ConnectionInfo, Connector]]: The consumers of the workflow.
        """
        return self.workflow_consumers[workflow_name]
    
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
    
