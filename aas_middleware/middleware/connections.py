import typing
from pydantic import BaseModel, ConfigDict

from aas_middleware.connect.connectors.connector import Connector


class ConnectionInfo(BaseModel):
    """
    Class that contains the information of a connection of a provider and a consumer to the persistence layer.
    """
    data_model_name: str
    model_id: typing.Optional[str] = None
    field_id: typing.Optional[str] = None
    # TODO: add the type annotation of the connection type -> remove the type from provider / consumer, since it is used better here.... This allows to have a better overview of the connections
    # and also removes one layer of abstraction. Saves these connecction infos in classes that make dict based mappings and queries on their attributes possible
    # Also think about saving these connectionInfos as meta data. 
    model_type : typing.Optional[typing.Type[typing.Any]] = None

    model_config = ConfigDict(frozen=True, protected_namespaces=())

    @property
    def connection_type(self) -> typing.Literal["data_model", "model", "field"]:
        if self.model_id:
            if self.field_id:
                return "field"
            return "model"
        return "data_model"
    
class ConnectionManager(BaseModel):
    """
    Class that manages the connections of the middleware.
    """
    connections: typing.Dict[ConnectionInfo, typing.List[Connector]] = {}

    data_model_connection_infos: typing.Dict[str, typing.List[ConnectionInfo]] = []
    model_connection_infos: typing.Dict[str, typing.List[ConnectionInfo]] = []
    field_connection_infos: typing.Dict[str, typing.List[ConnectionInfo]] = []
    type_connection_infos: typing.Dict[str, typing.List[ConnectionInfo]] = []

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
        return self.type_connection_infos[type_name]
    

class PersistenceConnectionManager(ConnectionManager):
    """
    Class that manages the connections of the middleware.
    """
    connections: typing.Dict[ConnectionInfo, Connector] = {}

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
                self.data_model_connection_infos[connection_info.data_model_name] = set()
            self.data_model_connection_infos[connection_info.data_model_name].append(connection_info)
        elif connection_info.connection_type == "model":
            if not connection_info.model_id in self.model_connection_infos:
                self.model_connection_infos[connection_info.model_id] = set()
            self.model_connection_infos[connection_info.model_id].append(connection_info)  
        elif connection_info.connection_type == "field":
            if not connection_info.field_id in self.field_connection_infos:
                self.field_connection_infos[connection_info.field_id] = set()
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
        return self.connections[connection_info]


    


