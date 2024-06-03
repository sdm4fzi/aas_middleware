

from functools import partial
from typing import Tuple, Type

from aas_middleware.connect.connectors.connector import Connector
from aas_middleware.model.core import Identifiable


class PersistenceFactory:

    def __init__(self, connector_type: Type[Connector], *args, **kwargs):
        self.connector = partial(connector_type, *args, **kwargs)
    
    def create(self, model: Identifiable, *args, **kwargs) -> Connector:
        connector = self.connector(model, *args, **kwargs)
        return connector
        