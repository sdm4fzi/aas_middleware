

from functools import partial
from typing import Tuple, Type

from aas_middleware.connect.connectors.connector import Connector
from aas_middleware.connect.consumers.connector_consumer import ConnectorConsumer
from aas_middleware.connect.consumers.consumer import Consumer
from aas_middleware.connect.providers.connector_provider import ConnectorProvider
from aas_middleware.connect.providers.provider import Provider
from aas_middleware.model.core import Identifiable


class PersistenceFactory:

    def __init__(self, connector_type: Type[Connector], *args, **kwargs):
        self.connector = partial(connector_type, *args, **kwargs)
    
    def create(self, model: Identifiable, *args, **kwargs) -> Tuple[Consumer, Provider]:
        connector = self.connector(model, *args, **kwargs)
        consumer = ConnectorConsumer(connector, type(model), model.id)
        provider = ConnectorProvider(connector, type(model), model.id)
        return consumer, provider
        