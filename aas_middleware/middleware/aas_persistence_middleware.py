from __future__ import annotations

from aas_middleware.connect.connectors.aas_client_connector.aas_client_connector import BasyxAASConnector, BasyxSubmodelConnector
from aas_middleware.middleware.middleware import Middleware
from aas_middleware.middleware.persistence_factory import PersistenceFactory
from aas_middleware.model.data_model import DataModel
from aas_middleware.model.data_model_rebuilder import DataModelRebuilder
from aas_middleware.model.formatting.aas.aas_model import AAS, Submodel

class AasMiddleware(Middleware):
    """
    Middleware that automatically that has aas and submodel repositories as persistence providers and consumers.
    """

    def __init__(self):
        super().__init__()

    def load_aas_persistent_data_model(self, name: str, data_model: DataModel, aas_host: str, aas_port: int, submodel_host: str, submodel_port: int):
        """
        Function to load a data model into the middleware to be used for synchronization.

        Args:
            name (str): The name of the data model.
            data_model (DataModel): Data model containing the types and values.
            aas_host (str): The host of the AAS server.
            aas_port (int): The port of the AAS server.
            submodel_host (str): The host of the submodel server.
            submodel_port (int): The port of the submodel server.
        """
        aas_data_model = DataModelRebuilder(data_model).rebuild_data_model_for_AAS_structure()
        self.load_data_model(name, aas_data_model)
        # TODO: resolve this later with types in data model
        aas_persistence_factory = PersistenceFactory(BasyxAASConnector, host=aas_host, port=aas_port, submodel_host=submodel_host, submodel_port=submodel_port)
        submodel_persistence_factory = PersistenceFactory(BasyxSubmodelConnector, host=submodel_host, port=submodel_port)

        for models_of_type in aas_data_model.get_top_level_models().values():
            if not models_of_type:
                continue
            model = models_of_type[0]

            if isinstance(model, AAS):
                persistence_factory = aas_persistence_factory
            elif isinstance(model, Submodel):
                persistence_factory = submodel_persistence_factory
            else:
                raise ValueError("Model is not of type AAS or Submodel")
            
            if not name in self.persistence_factories:
                self.persistence_factories[name] = {}
            class_name = model.__class__.__name__

            # TODO: save persistence factory in persistence manager...
            self.persistence_factories[name][class_name] = persistence_factory

            for model in models_of_type:
                self.create_persistence(name, model, persistence_factory)
                self.add_callback("on_start_up", self.update_value, model, name, model.id)
        
        self.generate_rest_api_for_data_model(name)

    def scan_aas_server(self):
        """
        Function to scan the AAS server for all available AAS and Submodels.
        """
        # TODO: implement function
        pass