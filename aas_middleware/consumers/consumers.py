from typing import Type, TypeVar, Generic

from aas_middleware.core import Connector
from aas_middleware.data_model import base

C = TypeVar("C", bound=Connector)
D = TypeVar("D", bound=base.Identifiable)

class Consumer(Generic[C, D]):
    def __init__(self, connector: C, data_model: Type[D]) -> None:
        self.connector = connector
        self.data_model = data_model

    async def set_connector(self, connector: C):
        self.connector = connector

    async def get_connector(self) -> C:
        return self.connector
    
    async def set_model(self, model: Type[D]):
        self.data_model = model

    async def get_model(self) -> Type[D]:
        return self.data_model
    
    async def execute(self, data: D):
        # TODO: make validation of data
        body = data.json()
        respone = await self.connector.send(body)
        print(respone)