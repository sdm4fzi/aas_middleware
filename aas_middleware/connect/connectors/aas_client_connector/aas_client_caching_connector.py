import asyncio
from typing import Generic, Optional, TypeVar

from aas_middleware.connect.connectors.aas_client_connector.aas_client_connector import (
    BasyxAASConnector,
    BasyxSubmodelConnector,
)
from aas_pydantic.aas_model import AAS, Submodel

T = TypeVar("T", bound=AAS)
S = TypeVar("S", bound=Submodel)


class BasyxAASCachingConnector(Generic[T]):
    """
    Caching wrapper that reuses a single BasyxAASConnector instance.
    """

    def __init__(
        self,
        model: T,
        host: str,
        port: int,
        submodel_host: Optional[str] = None,
        submodel_port: Optional[int] = None,
        max_connections: int = 64,
    ):
        self._core = BasyxAASConnector(
            model=model,
            host=host,
            port=port,
            submodel_host=submodel_host,
            submodel_port=submodel_port,
            max_connections=max_connections,
        )
        self._cached: Optional[T] = model

    async def connect(self) -> None:
        await self._core.connect()

    async def disconnect(self) -> None:
        await self._core.disconnect()

    async def consume(self, body: Optional[T]) -> None:
        self._cached = body
        await self._core.consume(body)

    async def provide(self) -> T:
        if self._cached is None:
            return await self._core.provide()
        return self._cached


class BasyxSubmodelCachingConnector(Generic[S]):
    """
    Caching wrapper that reuses a single BasyxSubmodelConnector instance.
    """

    def __init__(
        self,
        submodel: S,
        host: str,
        port: int,
        max_connections: int = 64,
    ):
        self._core = BasyxSubmodelConnector(
            submodel=submodel,
            host=host,
            port=port,
            max_connections=max_connections,
        )
        self._cached: Optional[S] = submodel

    async def connect(self) -> None:
        await self._core.connect()

    async def disconnect(self) -> None:
        await self._core.disconnect()

    async def consume(self, body: Optional[S]) -> None:
        self._cached = body
        asyncio.create_task(self._core.consume(body))

    async def provide(self) -> S:
        if self._cached is None:
            return await self._core.provide()
        return self._cached
