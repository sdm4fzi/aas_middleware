from __future__ import annotations
import json
from typing import Any, Dict, List, Literal

import basyx.aas
from aas_middleware.model.data_model import DataModel


from aas_middleware.model.formatting.aas.aas_model import BasyxModels
from basyx.aas.model import DictObjectStore
from basyx.aas import model
import basyx.aas.adapter.json


from aas_middleware.model.formatting.aas.basyx_formatter import BasyxFormatter
from aas_middleware.model.formatting.aas.convert_aas import (
    convert_aas_to_pydantic_model,
    convert_object_store_to_pydantic_models,
)
from aas_middleware.model.formatting.aas.convert_pydantic import (
    convert_model_to_aas,
    convert_model_to_submodel,
    infere_aas_structure,
)


class AasJsonFormatter:
    """
    Allows to serialize and deserialize Basyx AAS objects (AssetAdministrationShells, Submodels or Containers of both) to a DataModel.
    """

    def serialize(self, data: DataModel) -> Dict[Literal["assetAdministrationShells", "submodels"], List[str]]:
        """
        Serialize a DataModel object to the specific format of the formatter.

        Args:
            data (DataModel): A data model

        Returns:
            Objectstore: the basyx object store contain all AAS elements
        """
        basyx_dict_obj_store = BasyxFormatter().serialize(data)
        return json.loads(basyx.aas.adapter.json.object_store_to_json(basyx_dict_obj_store))


    def deserialize(self, data: Dict[Literal["assetAdministrationShells", "submodels"], List[str]]) -> DataModel:
        """
        Deserialize the specific format of the formater to a DataModel object.

        Args:
            data (Any): The specific format of the formatter.

        Returns:
            DataModel: A data model that holds the objects that were deserialized
        """
        object_store = DictObjectStore()
        for key, items in data.items():
            if key == "assetAdministrationShells":
                for aas_item in items:
                    aas = json.loads(json.dumps(aas_item), cls=basyx.aas.adapter.json.AASFromJsonDecoder)
                    object_store.add(aas)
            elif key == "submodels":
                for submodel_item in items:
                    submodel = json.loads(json.dumps(submodel_item), cls=basyx.aas.adapter.json.AASFromJsonDecoder)
                    object_store.add(submodel)
        return BasyxFormatter().deserialize(object_store)
        

        
