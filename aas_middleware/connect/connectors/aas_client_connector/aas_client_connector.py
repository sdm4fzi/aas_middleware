
from typing import Generic, Optional, TypeVar
from aas_middleware.connect.connectors.aas_client_connector.aas_client import aas_is_on_server, delete_aas_from_server, get_aas_from_server, post_aas_to_server, put_aas_to_server

from ba_syx_aas_environment_component_client import Client as AASClient
from ba_syx_aas_environment_component_client import Client as SubmodelClient

from aas_middleware.connect.connectors.aas_client_connector.client_utils import check_aas_and_sm_server_online, check_sm_server_online
from aas_middleware.connect.connectors.aas_client_connector.submodel_client import delete_submodel_from_server, get_submodel_from_server, post_submodel_to_server, put_submodel_to_server, submodel_is_on_server
from aas_middleware.model.formatting.aas.aas_model import AAS, Submodel

T = TypeVar("T", bound=AAS)
S = TypeVar("S", bound=Submodel)

class BasyxAASConnector(Generic[T]):
    def __init__(self, aas_id: str, host: str, port: int, submodel_host: Optional[str] = None, submodel_port: Optional[int] = None):
        # TODO: aas and submodel repo host are needed as kwargs
        self.host = host
        self.port = port
        self.aas_id = aas_id

        if not submodel_host:
            submodel_host = host
        self.submodel_host = submodel_host

        if not submodel_port:
            submodel_port = port
        self.submodel_port = submodel_port
        self.aas_server_address = f"http://{host}:{port}"
        self.submodel_server_address = f"http://{submodel_host}:{submodel_port}"

        self.aas_client = AASClient(base_url=self.aas_server_address)
        # TODO: make it possible that multiple submodel clients can be used mapped to different submodel repos for different submodels by their id
        self.submodel_client = SubmodelClient(base_url=self.submodel_server_address)

    async def connect(self):
        await check_aas_and_sm_server_online(self.aas_server_address, self.submodel_server_address)

    async def disconnect(self):
        pass

    async def send(self, body: Optional[T]) -> None:
        if not body:
            await delete_aas_from_server(self.aas_id, self.aas_client)
        if aas_is_on_server(self.aas_id, self.aas_client):
            put_aas_to_server(self.aas_id, self.aas_client, self.submodel_client)
        else:
            post_aas_to_server(self.aas_id, self.aas_client, self.submodel_client)

    async def receive(self) -> T:
        return await get_aas_from_server(self.aas_id, self.aas_client, self.submodel_client)


class BasyxSubmodelConnector(Generic[S]):
    def __init__(self, submodel_id: str, host: str, port: int):
        self.host = host
        self.port = port
        self.submodel_id = submodel_id

        self.submodel_server_address = f"http://{host}:{port}"

        self.submodel_client = SubmodelClient(base_url=self.submodel_server_address)

    async def connect(self):
        await check_sm_server_online(self.submodel_server_address)

    async def disconnect(self):
        pass

    async def send(self, body: Optional[S]) -> None:
        if not body:
            await delete_submodel_from_server(self.submodel_id, self.submodel_client)
        if submodel_is_on_server(self.submodel_id, self.submodel_client):
            put_submodel_to_server(self.submodel_id, self.submodel_client)
        else:
            post_submodel_to_server(self.submodel_id, self.submodel_client)

    async def receive(self) -> S:
        return await get_submodel_from_server(self.submodel_id, self.submodel_client)