from typing import Generic, Type
from aas_middleware.connect.connectors.connector import Connector
from aas_middleware.connect.providers.provider import D

class ConnectorProvider(Generic[D]):
    def __init__(self, connector: Connector, data_model: Type[D], id: str) -> None:
        self.connector = connector
        self.data_model = data_model
        self._id = id
        # TODO: connect connector

    @property
    def id(self) -> str:
        return self._id

    def set_connector(self, connector: Connector):
        self.connector = connector

    def get_connector(self) -> Connector:
        return self.connector

    def set_model(self, model: Type[D]):
        self.data_model = model

    def get_model(self) -> Type[D]:
        return self.data_model

    async def execute(self) -> D:
        response = await self.connector.receive()
        return self.data_model.model_validate(response)


class QueryConnectorProvider(Generic[D]):
    """
    Allows to execute with a query on the connector instead of a preloaded adress for querying.
    """


class MultiConnectorProvider(Generic[D]):
    """
    Provider with multiple connectors to get data from.
    """

    pass
