from typing import Any, Awaitable, Coroutine, Protocol, TypeVar, Generic, Type
from aas_middleware.connect.connectors.connector import Connector
from aas_middleware.model import core

D = TypeVar("D", bound=core.Identifiable)

class Provider(Protocol, Generic[D]):
    @property
    def item_id(self) -> str:
        ...

    def set_model(self, model: Type[D]):
        ...

    def get_model(self) -> Type[D]:
        ...

    async def execute(self) -> D:
        ...



class ConnectorProvider(Generic[D]):
    def __init__(self, connector: Connector, data_model: Type[D], id: str) -> None:
        self.connector = connector
        self.data_model = data_model
        self.id = id
        # TODO: connect connector

    @property
    def id(self) -> str:
        return self.id

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
        return self.data_model.model_validate_json(response)


class QueryConnectorProvider(Generic[D]):
    """
    Allows to execute with a query on the connector instead of a preloaded adress for querying.
    """


class MultiConnectorProvider(Generic[D]):
    """
    Provider with multiple connectors to get data from.
    """

    pass
