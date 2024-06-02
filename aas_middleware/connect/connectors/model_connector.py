
from typing import Generic, Optional, TypeVar
from aas_middleware.connect.connectors.aas_client_connector.aas_client import aas_is_on_server, delete_aas_from_server, get_aas_from_server, post_aas_to_server, put_aas_to_server

from ba_syx_aas_environment_component_client import Client as AASClient
from ba_syx_aas_environment_component_client import Client as SubmodelClient

from aas_middleware.connect.connectors.aas_client_connector.client_utils import check_aas_and_sm_server_online, check_sm_server_online
from aas_middleware.connect.connectors.aas_client_connector.submodel_client import delete_submodel_from_server, get_submodel_from_server, post_submodel_to_server, put_submodel_to_server, submodel_is_on_server
from aas_middleware.model.core import Identifiable
from aas_middleware.model.formatting.aas.aas_model import AAS, Submodel

T = TypeVar("T", bound=Identifiable)

class ModelConnector(Generic[T]):
    def __init__(self, model: Optional[Identifiable]):
        self.model = model

    async def connect(self):
        pass

    async def disconnect(self):
        pass

    async def send(self, body: Optional[T]) -> None:
        if not body:
            self.model = None

    async def receive(self) -> Optional[T]:
        return self.model