from __future__ import annotations

from aas_middleware.connect.connectors.aas_client_connector.aas_client_caching_connector import (
    BasyxAASCachingConnector,
    BasyxSubmodelCachingConnector,
)
from aas_middleware.connect.connectors.aas_client_connector.aas_client_connector import (
    BasyxAASConnector,
    BasyxSubmodelConnector,
)
from aas_middleware.middleware.middleware import Middleware
from aas_middleware.middleware.persistence_factory import PersistenceFactory
from aas_middleware.model.data_model import DataModel
from aas_middleware.model.data_model_rebuilder import DataModelRebuilder
from aas_pydantic.aas_model import AAS, Submodel


class AasMiddleware(Middleware):
    """
    Middleware that automatically that has aas and submodel repositories as persistence providers and consumers.
    """

    def __init__(self):
        super().__init__()

    def load_aas_persistent_data_model(
        self,
        name: str,
        data_model: DataModel,
        aas_host: str,
        aas_port: int,
        submodel_host: str,
        submodel_port: int,
        persist_instances: bool = False,
        caching: bool = False,
    ):
        """
        Function to load a data model into the middleware to be used for synchronization.

        Args:
            name (str): The name of the data model.
            data_model (DataModel): Data model containing the types and values.
            aas_host (str): The host of the AAS server.
            aas_port (int): The port of the AAS server.
            submodel_host (str): The host of the submodel server.
            submodel_port (int): The port of the submodel server.
            persist_instances (bool, optional): Whether to persist instances of the data model. Defaults to False.
        """
        # aas_data_model = DataModelRebuilder(data_model).rebuild_data_model_for_AAS_structure()
        aas_data_model = data_model
        self.load_data_model(name, aas_data_model, persist_instances)

        if caching:
            aas_connector = BasyxAASCachingConnector
            submodel_connector = BasyxSubmodelCachingConnector

        else:
            aas_connector = BasyxAASConnector
            submodel_connector = BasyxSubmodelConnector

        aas_persistence_factory = PersistenceFactory(
            aas_connector,
            host=aas_host,
            port=aas_port,
            submodel_host=submodel_host,
            submodel_port=submodel_port,
        )
        submodel_persistence_factory = PersistenceFactory(
            submodel_connector, host=submodel_host, port=submodel_port
        )
        self.add_default_persistence(aas_persistence_factory, name, None, AAS)
        self.add_default_persistence(submodel_persistence_factory, name, None, Submodel)

    def scan_aas_server(self):
        """
        Function to scan the AAS server for all available AAS and Submodels.
        """
        # TODO: implement function
        pass
