from typing import Any, Awaitable, Coroutine, TypeVar, Generic, Type
from aas_middleware.core import Connector
from aas_middleware.model import core

C = TypeVar("C", bound=Connector)
D = TypeVar("D", bound=core.Referable)


class ConnectorProvider(Generic[D]):
    def __init__(self, connector: Connector, data_model: Type[D]) -> None:
        self.connector = connector
        self.data_model = data_model

    def set_connector(self, connector: Connector):
        self.connector = connector

    def get_connector(self) -> Connector:
        return self.connector

    def set_model(self, model: Type[D]):
        self.data_model = model

    def get_model(self) -> Type[D]:
        return self.data_model

    async def execute(self) -> Coroutine[Any, Any, D]:
        response = await self.connector.receive()
        return self.data_model.parse_raw(response)


class QueryConnectorProvider(Generic[D]):
    """
    Allows to execute with a query on the connector instead of a preloaded adress for querying.
    """


class MultiConnectorProvider(Generic[D]):
    """
    Provider with multiple connectors to get data from.
    """

    pass
