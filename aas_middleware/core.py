from typing import Protocol, Optional, Type, TypeVar
from aas_middleware.data_model import base

class Connector(Protocol):
    async def connect(self):
        ...

    async def disconnect(self):
        ...

    async def send(self, body: str) -> Optional[str]:
        ...

    async def receive(self) -> str:
        ...

D = TypeVar("D", bound=base.Identifiable)
D2 = TypeVar("D2", bound=base.Identifiable)

class Actor(Protocol[D]):
    def set_model(self, model: Type[D]):
        ...

    def get_model(self) -> Type[D]:
        ...

class Persistence(Actor[D], Protocol):
    async def save(self, data: D):
        ...

    async def load(self, id: str) -> D:
        ...

    async def delete(self, id: str):
        ...


class Provider(Actor[D], Protocol):
    async def execute(self) -> D:
        ...

    
class Consumer(Actor[D], Protocol):
    async def execute(self, data: D):
        ...


class Processor(Protocol[D, D2]):
    async def execute(self, data: D) -> D2:
        ...

    def set_input_model(self, model: Type[D]):
        ...

    def get_input_model(self) -> Type[D]:
        ...

    def set_output_model(self, model: Type[D2]):
        ...

    def get_output_model(self) -> Type[D2]:
        ...

class Callback(Protocol[D]):
    async def pre_callback(self) -> D:
        ...

    async def post_callback(self, data: D):
        ...