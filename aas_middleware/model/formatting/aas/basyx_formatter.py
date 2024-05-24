from __future__ import annotations
from typing import Any, List

import basyx.aas
from aas_middleware.model.data_model import DataModel


from aas_middleware.model.formatting.aas.aas_model import BasyxModels
from basyx.aas.model import DictObjectStore
from basyx.aas import model

from aas_middleware.model.formatting.aas.convert_aas import (
    convert_aas_to_pydantic_model,
    convert_object_store_to_pydantic_models,
)
from aas_middleware.model.formatting.aas.convert_pydantic import (
    convert_model_to_aas,
    convert_model_to_submodel,
    infere_aas_structure,
)


# TODO: rename to basyx formatter
class BasyxFormatter:
    """
    Allows to serialize and deserialize Basyx AAS objects (AssetAdministrationShells, Submodels or Containers of both) to a DataModel.
    """

    def serialize(self, data: DataModel) -> DictObjectStore[model.Identifiable]:
        """
        Serialize a DataModel object to the specific format of the formatter.

        Args:
            data (DataModel): A data model

        Returns:
            Objectstore: the basyx object store contain all AAS elements
        """
        aas_models, submodel_models = infere_aas_structure(data)
        obj_store = DictObjectStore()
        for aas in aas_models:
            obj_store_to_add = convert_model_to_aas(aas)
            for identifiable in obj_store_to_add:
                if obj_store.get(identifiable.id_short) is not None:
                    continue
                obj_store.add(identifiable)
        for submodel in submodel_models:
            submodel_to_add = convert_model_to_submodel(submodel)
            if obj_store.get(submodel_to_add.id_short) is not None:
                continue
            obj_store.add(submodel_to_add)
        return obj_store

    def deserialize(self, data: BasyxModels) -> DataModel:
        """
        Deserialize the specific format of the formater to a DataModel object.

        Args:
            data (Any): The specific format of the formatter.

        Returns:
            DataModel: A data model that holds the objects that were deserialized
        """
        if not isinstance(data, DictObjectStore):
            data = DictObjectStore(data)
        models = convert_object_store_to_pydantic_models(data)
        return DataModel.from_models(*models)
