import asyncio
from typing import Generic, Optional, TypeVar

import anyio
from anyio.abc._tasks import TaskGroup

from fastapi import HTTPException
from aas_middleware.connect.connectors.aas_client_connector.aas_client import (
    aas_is_on_server,
    delete_aas_from_server,
    get_aas_from_server,
    post_aas_to_server,
    put_aas_to_server,
)

from ba_syx_aas_environment_component_client import Client as AASClient
from ba_syx_aas_environment_component_client import Client as SubmodelClient

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


class BasyxAASCachingConnector(Generic[T]):
    def __init__(
        self,
        model: T,
        host: str,
        port: int,
        submodel_host: Optional[str] = None,
        submodel_port: Optional[int] = None,
    ):
        self.host = host
        self.port = port
        self.aas_id = model.id
        self.aas_type_template: Optional[T] = type(model)

        self.cached_model: Optional[T] = None

        if not submodel_host:
            submodel_host = host
        self.submodel_host = submodel_host

        if not submodel_port:
            submodel_port = port
        self.submodel_port = submodel_port
        self.aas_server_address = f"http://{host}:{port}"
        self.submodel_server_address = f"http://{submodel_host}:{submodel_port}"

    @property
    def aas_client(self):
        return AASClient(base_url=self.aas_server_address)

    @property
    def submodel_client(self):
        return SubmodelClient(base_url=self.submodel_server_address)

    async def connect(self):
        await check_aas_and_sm_server_online(
            self.aas_server_address, self.submodel_server_address
        )

    async def disconnect(self):
        pass

    async def consume_on_server(self, body: Optional[T]) -> None:
        try:
            if not body:
                await delete_aas_from_server(self.aas_id, self.aas_client)
            elif await aas_is_on_server(self.aas_id, self.aas_client):
                await put_aas_to_server(body, self.aas_client, self.submodel_client)
            else:
                await post_aas_to_server(body, self.aas_client, self.submodel_client)
        except Exception as e:
            raise ConnectionError(f"Error consuming AAS: {e}")

    async def consume(self, body: Optional[T]) -> None:
        if body and body.id != self.aas_id:
            self.aas_id = body.id
        if not self.aas_type_template:
            self.aas_type_template = type(body)
        self.cached_model = body
        asyncio.create_task(self.consume_on_server(body))

    async def provide(self) -> T:
        if not self.cached_model:
            raise ConnectionError(
                f"No model is consumed until now for this connector. Either consume first a model or use the non caching basyx connector."
            )
        return self.cached_model


class BasyxSubmodelCachingConnector(Generic[S]):
    def __init__(self, submodel: S, host: str, port: int):
        self.host = host
        self.port = port
        self.submodel_id = submodel.id
        self.submodel_type_template = type(submodel)

        self.cached_model: Optional[S] = None

        self.submodel_server_address = f"http://{host}:{port}"

        self.submodel_client = SubmodelClient(base_url=self.submodel_server_address)

    async def connect(self):
        await check_sm_server_online(self.submodel_server_address)

    async def disconnect(self):
        pass

    async def consume_on_server(self, body: Optional[T]) -> None:
        try:
            if not body:
                await delete_submodel_from_server(
                    self.submodel_id, self.submodel_client
                )
            elif await submodel_is_on_server(self.submodel_id, self.submodel_client):
                await put_submodel_to_server(self.submodel_id, self.submodel_client)
            else:
                await post_submodel_to_server(self.submodel_id, self.submodel_client)
        except Exception as e:
            raise ConnectionError(f"Error consuming Submodel: {e}")

    async def consume(self, body: Optional[S]) -> None:
        if body and body.id != self.submodel_id:
            self.submodel_id = body.id
        if not self.submodel_type_template:
            self.submodel_type_template = type(body)
        self.cached_model = body
        asyncio.create_task(self.consume_on_server(body))

    async def provide(self) -> T:
        if not self.cached_model:
            raise ConnectionError(
                f"No model is consumed until now for this connector. Either consume first a model or use the non caching basyx connector."
            )
        return self.cached_model
