from typing import Protocol, Type, TypeVar, Generic
from aas_middleware.connect.connectors.connector import Connector
from aas_middleware.model import core

D = TypeVar("D", bound=core.Identifiable)

class Consumer(Protocol, Generic[D]):
    @property
    def item_id(self) -> str:
        ...

    def set_model(self, model: Type[D]):
        ...

    def get_model(self) -> Type[D]:
        ...

    async def execute(self, data: D):
        ...



class ConnectorConsumer(Generic[D]):
    def __init__(self, connector: Connector, data_model: Type[D], id: str) -> None:
        self.connector = connector
        self.data_model = data_model
        self.id = id
        # TODO: connect connector

    @property
    def id(self) -> str:
        return self.id

    async def set_connector(self, connector: Connector):
        self.connector = connector

    async def get_connector(self) -> Connector:
        return self.connector

    async def set_model(self, model: Type[D]):
        self.data_model = model

    async def get_model(self) -> Type[D]:
        return self.data_model

    async def execute(self, data: D):
        self.data_model.model_validate(data)
        body = data.model_dump_json()
        respone = await self.connector.send(body)
