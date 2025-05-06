import asyncio
from typing import Any, Generic, Optional, TypeVar, Dict

from httpx import Limits
from fastapi import HTTPException
from aas_middleware.connect.connectors.aas_client_connector.aas_client import (
    aas_is_on_server,
    delete_aas_from_server,
    get_aas_from_server,
    post_aas_to_server,
    put_aas_to_server,
)

from ba_syx_aas_environment_component_client import Client as BasyxClient

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
from aas_pydantic.aas_model import AAS, Submodel

T = TypeVar("T", bound=AAS)
S = TypeVar("S", bound=Submodel)


def _default_httpx_args(max_conn: int) -> Dict[str, Any]:
    # default to HTTP/2 multiplexing with a pool of keep-alive connections
    return {
        "limits": Limits(
            max_connections=max_conn, max_keepalive_connections=max_conn // 2
        ),
        "http2": True,
    }


class _SharedClientManager:
    """
    Keeps one AsyncClient per base_url alive across all connector instances,
    optionally with injected httpx_args.
    """

    _clients: Dict[str, BasyxClient] = {}

    @classmethod
    def get_client(
        cls,
        base_url: str,
        httpx_args: Optional[Dict[str, Any]] = None,
    ) -> BasyxClient:
        if base_url not in cls._clients:
            init_args: Dict[str, Any] = {"base_url": base_url}
            if httpx_args:
                init_args["httpx_args"] = httpx_args
            cls._clients[base_url] = BasyxClient(**init_args)
        return cls._clients[base_url]

    @classmethod
    async def close_all(cls) -> None:
        # Call this once on application shutdown
        for client in cls._clients.values():
            await client.aclose()
        cls._clients.clear()


class BasyxAASConnector(Generic[T]):
    """
    Connector for AAS objects with global concurrency limit
    and httpx_args injection.
    """

    _semaphore: asyncio.Semaphore | None = None
    _max_connections: int = 32

    def __init__(
        self,
        model: T,
        host: str,
        port: int,
        submodel_host: Optional[str] = None,
        submodel_port: Optional[int] = None,
        max_connections: int = 32,
        httpx_args: Optional[Dict[str, Any]] = None,
    ):
        # Initialize or update class-level semaphore once
        if self.__class__._semaphore is None:
            self.__class__._max_connections = max_connections
            self.__class__._semaphore = asyncio.Semaphore(max_connections)

        # Compute default httpx_args if not provided
        if httpx_args is None:
            httpx_args = _default_httpx_args(self.__class__._max_connections)

        self.host = host
        self.port = port
        self.aas_id = model.id
        self.aas_type_template: Optional[T] = type(model)
        self._httpx_args = httpx_args

        if not submodel_host:
            submodel_host = host
        self.submodel_host = submodel_host

        if not submodel_port:
            submodel_port = port
        self.submodel_port = submodel_port
        self.aas_server_address = f"http://{host}:{port}"
        self.submodel_server_address = f"http://{submodel_host}:{submodel_port}"

        # Use httpx_args when creating shared clients
        self._aas_client = _SharedClientManager.get_client(
            self.aas_server_address, httpx_args=self._httpx_args
        )
        self._submodel_client = _SharedClientManager.get_client(
            self.submodel_server_address, httpx_args=self._httpx_args
        )

    async def connect(self):
        await check_aas_and_sm_server_online(
            self.aas_server_address, self.submodel_server_address
        )

    async def disconnect(self):
        await _SharedClientManager.close_all()

    async def consume(self, body: Optional[T]) -> None:
        sem = self.__class__._semaphore
        assert sem is not None, "Semaphore not initialized"
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
                        body, self._aas_client, self._submodel_client
                    )
                else:
                    await post_aas_to_server(
                        body, self._aas_client, self._submodel_client
                    )
            except Exception as e:
                raise ConnectionError(f"Error consuming AAS: {e}") from e

    async def provide(self) -> T:
        sem = self.__class__._semaphore
        assert sem is not None, "Semaphore not initialized"
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
    and httpx_args injection.
    """

    _semaphore: asyncio.Semaphore | None = None
    _max_connections: int = 32

    def __init__(
        self,
        submodel: S,
        host: str,
        port: int,
        max_connections: int = 32,
        httpx_args: Optional[Dict[str, Any]] = None,
    ):
        # Initialize or update class-level semaphore once
        if self.__class__._semaphore is None:
            self.__class__._max_connections = max_connections
            self.__class__._semaphore = asyncio.Semaphore(max_connections)

        # Compute default httpx_args if not provided
        if httpx_args is None:
            httpx_args = _default_httpx_args(self.__class__._max_connections)

        self.host = host
        self.port = port
        self.submodel_id = submodel.id
        self.submodel_type_template = type(submodel)
        self._httpx_args = httpx_args

        self.submodel_server_address = f"http://{host}:{port}"
        self._submodel_client = _SharedClientManager.get_client(
            self.submodel_server_address, httpx_args=self._httpx_args
        )

    async def connect(self):
        await check_sm_server_online(self.submodel_server_address)

    async def disconnect(self):
        await _SharedClientManager.close_all()

    async def consume(self, body: Optional[S]) -> None:
        sem = self.__class__._semaphore
        assert sem is not None, "Semaphore not initialized"
        async with sem:
            if body and body.id != self.submodel_id:
                self.submodel_id = body.id
            if not self.submodel_type_template:
                self.submodel_type_template = type(body)
            try:
                if not body:
                    await delete_submodel_from_server(
                        self.submodel_id, self._submodel_client
                    )
                elif await submodel_is_on_server(
                    self.submodel_id, self._submodel_client
                ):
                    await put_submodel_to_server(body, self._submodel_client)
                else:
                    await post_submodel_to_server(body, self._submodel_client)
            except Exception as e:
                raise ConnectionError(f"Error consuming Submodel: {e}") from e

    async def provide(self) -> S:
        sem = self.__class__._semaphore
        assert sem is not None, "Semaphore not initialized"
        async with sem:
            try:
                return await get_submodel_from_server(
                    self.submodel_id, self._submodel_client, self.submodel_type_template
                )
            except Exception as e:
                raise ConnectionError(f"Error providing Submodel: {e}") from e
