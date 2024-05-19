from typing import Protocol, TypeVar, Generic, Type
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
