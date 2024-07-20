
from typing import Generic, Optional, TypeVar


from aas_middleware.model.core import Identifiable

T = TypeVar("T", bound=Identifiable)

class ModelConnector(Generic[T]):
    def __init__(self, model: Optional[Identifiable]):
        self.model = model

    async def connect(self):
        pass

    async def disconnect(self):
        pass

    async def consume(self, body: Optional[T]) -> None:
        if not body:
            self.model = None
        else:
            self.model = body

    async def provide(self) -> Optional[T]:
        return self.model