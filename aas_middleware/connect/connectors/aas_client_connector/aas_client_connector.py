import asyncio
from typing import Any, Dict, Generic, Optional, TypeVar

import httpx
from httpx import AsyncClient, Limits
from fastapi import HTTPException

from aas_middleware.connect.connectors.aas_client_connector.aas_client import (
    aas_is_on_server,
    delete_aas_from_server,
    get_aas_from_server,
    post_aas_to_server,
    put_aas_to_server,
)
from aas_middleware.connect.connectors.aas_client_connector.client_utils import (
    check_aas_and_sm_server_online,
    check_sm_server_online,
)
from aas_middleware.connect.connectors.aas_client_connector.submodel_client import (
    delete_submodel_from_server,
    get_submodel_from_server,
    post_submodel_to_server,
    put_submodel_to_server,
    submodel_is_on_server,
)
from ba_syx_aas_environment_component_client import Client as BasyxClient
from aas_pydantic.aas_model import AAS, Submodel

T = TypeVar("T", bound=AAS)
S = TypeVar("S", bound=Submodel)


def _default_httpx_args(max_conn: int) -> Dict[str, Any]:
    """
    Build default HTTPX arguments for connection pooling and HTTP/2.
    """
    return {
        "limits": Limits(
            max_connections=max_conn,
            max_keepalive_connections=max_conn,
        )
    }


class _SharedClientManager:
    """
    Keeps one AsyncClient per base_url alive across all connector instances.

    Ensures a single BasyxClient wrapping an injected AsyncClient
    pool, with preconfigured HTTP/2 and connection limits.
    """

    _clients: Dict[str, BasyxClient] = {}
    _httpx_args_map: Dict[str, Dict[str, Any]] = {}

    @classmethod
    def get_client(
        cls,
        base_url: str,
        httpx_args: Optional[Dict[str, Any]] = None,
    ) -> BasyxClient:
        # Determine args (use defaults if not provided)
        if httpx_args is None:
            raise ValueError("httpx_args must be provided for client initialization")

        # If we've seen this base_url before, ensure same configuration
        if base_url in cls._clients:
            prev_args = cls._httpx_args_map[base_url]
            if prev_args != httpx_args:
                raise ValueError(
                    f"Conflicting httpx_args for {base_url}: {prev_args} vs {httpx_args}"
                )
            return cls._clients[base_url]

        # First time seeing this base_url: create and inject AsyncClient
        # Build a BasyxClient wrapping our pool
        client = BasyxClient(base_url=base_url)
        async_pool = AsyncClient(
            base_url=base_url,
            **httpx_args,
        )
        client.set_async_httpx_client(async_pool)
        # Store
        cls._clients[base_url] = client
        cls._httpx_args_map[base_url] = httpx_args
        return client

    @classmethod
    async def close_all(cls) -> None:
        # Close every injected AsyncClient
        for client in cls._clients.values():
            # Extract underlying async client and close
            async_client = client.get_async_httpx_client()
            await async_client.aclose()
        cls._clients.clear()
        cls._httpx_args_map.clear()
    
    @classmethod
    async def close_client(cls, base_url: str) -> None:
        """Close a specific client by base_url"""
        if base_url in cls._clients:
            client = cls._clients[base_url]
            async_client = client.get_async_httpx_client()
            await async_client.aclose()
            del cls._clients[base_url]
            if base_url in cls._httpx_args_map:
                del cls._httpx_args_map[base_url]


class BasyxAASConnector(Generic[T]):
    """
    Connector for AAS objects with global concurrency limit
    and shared HTTPX async client per base URL.
    """

    _semaphore: asyncio.Semaphore | None = None
    _max_connections: int = 64

    def __init__(
        self,
        model: T,
        host: str,
        port: int,
        submodel_host: Optional[str] = None,
        submodel_port: Optional[int] = None,
        max_connections: int = 64,
    ):
        # Initialize or update class-level semaphore once
        if self.__class__._semaphore is None:
            self.__class__._max_connections = max_connections
            self.__class__._semaphore = asyncio.Semaphore(max_connections)

        # Compute default httpx_args
        httpx_args = _default_httpx_args(self.__class__._max_connections)

        self.host = host
        self.port = port
        self.aas_id = model.id
        self.aas_type_template: Optional[T] = type(model)

        # Determine submodel server
        if not submodel_host:
            submodel_host = host
        self.submodel_host = submodel_host
        if not submodel_port:
            submodel_port = port
        self.submodel_port = submodel_port

        # Build addresses
        self.aas_server_address = f"http://{host}:{port}"
        self.submodel_server_address = f"http://{submodel_host}:{submodel_port}"

        # Retrieve or create shared clients
        self._aas_client = _SharedClientManager.get_client(
            self.aas_server_address,
            httpx_args=httpx_args,
        )
        self._submodel_client = _SharedClientManager.get_client(
            self.submodel_server_address,
            httpx_args=httpx_args,
        )

    async def connect(self) -> None:
        await check_aas_and_sm_server_online(
            self.aas_server_address,
            self.submodel_server_address,
        )

    async def disconnect(self) -> None:
        # Don't close shared clients as they might be used by other connectors
        # The shared clients will be closed when the application shuts down
        pass

    async def consume(self, body: Optional[T]) -> None:
        sem = self.__class__._semaphore
        assert sem, "Semaphore not initialized"
        async with sem:
            if body and body.id != self.aas_id:
                self.aas_id = body.id
            if not self.aas_type_template:
                self.aas_type_template = type(body)
            try:
                if not body:
                    await delete_aas_from_server(self.aas_id, self._aas_client)
                elif await aas_is_on_server(self.aas_id, self._aas_client):
                    await put_aas_to_server(
                        body,
                        self._aas_client,
                        self._submodel_client,
                    )
                else:
                    await post_aas_to_server(
                        body,
                        self._aas_client,
                        self._submodel_client,
                    )
            except Exception as e:
                raise ConnectionError(f"Error consuming AAS: {e}") from e

    async def provide(self) -> T:
        sem = self.__class__._semaphore
        assert sem, "Semaphore not initialized"
        async with sem:
            try:
                return await get_aas_from_server(
                    self.aas_id,
                    self._aas_client,
                    self._submodel_client,
                    self.aas_type_template,
                )
            except Exception as e:
                raise ConnectionError(f"Error providing AAS: {e}") from e


class BasyxSubmodelConnector(Generic[S]):
    """
    Connector for Submodel objects with global concurrency limit
    and shared HTTPX async client per base URL.
    """

    _semaphore: asyncio.Semaphore | None = None
    _max_connections: int = 64

    def __init__(
        self,
        submodel: S,
        host: str,
        port: int,
        max_connections: int = 64,
    ):
        # Initialize or update class-level semaphore once
        if self.__class__._semaphore is None:
            self.__class__._max_connections = max_connections
            self.__class__._semaphore = asyncio.Semaphore(max_connections)

        httpx_args = _default_httpx_args(self.__class__._max_connections)

        self.host = host
        self.port = port
        self.submodel_id = submodel.id
        self.submodel_type_template = type(submodel)

        self.submodel_server_address = f"http://{host}:{port}"
        self._submodel_client = _SharedClientManager.get_client(
            self.submodel_server_address,
            httpx_args=httpx_args,
        )

    async def connect(self) -> None:
        await check_sm_server_online(self.submodel_server_address)

    async def disconnect(self) -> None:
        # Don't close shared clients as they might be used by other connectors
        # The shared clients will be closed when the application shuts down
        pass

    async def consume(self, body: Optional[S]) -> None:
        sem = self.__class__._semaphore
        assert sem, "Semaphore not initialized"
        async with sem:
            if body and body.id != self.submodel_id:
                self.submodel_id = body.id
            if not self.submodel_type_template:
                self.submodel_type_template = type(body)
            try:
                if not body:
                    await delete_submodel_from_server(
                        self.submodel_id,
                        self._submodel_client,
                    )
                elif await submodel_is_on_server(
                    self.submodel_id,
                    self._submodel_client,
                ):
                    await put_submodel_to_server(
                        body,
                        self._submodel_client,
                    )
                else:
                    await post_submodel_to_server(
                        body,
                        self._submodel_client,
                    )
            except Exception as e:
                raise ConnectionError(f"Error consuming Submodel: {e}") from e

    async def provide(self) -> S:
        sem = self.__class__._semaphore
        assert sem, "Semaphore not initialized"
        async with sem:
            try:
                return await get_submodel_from_server(
                    self.submodel_id,
                    self._submodel_client,
                    self.submodel_type_template,
                )
            except Exception as e:
                raise ConnectionError(f"Error providing Submodel: {e}") from e
