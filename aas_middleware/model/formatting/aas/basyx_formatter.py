from __future__ import annotations
from typing import List, Optional

from aas_middleware.model.data_model import DataModel


from aas_middleware.model.formatting.aas.aas_meta_model_inference import (
    infere_aas_structure,
)
from aas_pydantic.aas_model import AAS, BasyxModels, Submodel
from basyx.aas.model import DictObjectStore
from basyx.aas import model

from aas_pydantic.convert_pydantic_type import (
    convert_model_to_aas_template,
    convert_model_to_submodel_template,
)

from aas_pydantic.convert_pydantic_model import (
    convert_model_to_aas,
    convert_model_to_submodel,
)


from aas_pydantic.convert_aas_template import (
    convert_object_store_to_pydantic_types,
)

from aas_pydantic.convert_aas_instance import (
    convert_object_store_to_pydantic_models,
)


class BasyxTemplateFormatter:
    """
    Allows to serialize and deserialize Basyx AAS template objects (AssetAdministrationShells, Submodels or Containers of both) to a DataModel Template.
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
            obj_store_to_add = convert_model_to_aas_template(aas)
            for identifiable in obj_store_to_add:
                if obj_store.get(identifiable.id_short) is not None:
                    continue
                obj_store.add(identifiable)
        for submodel in submodel_models:
            submodel_to_add = convert_model_to_submodel_template(submodel)
            if obj_store.get(submodel_to_add.id_short) is not None:
                continue
            obj_store.add(submodel_to_add)
        return obj_store

    def deserialize(self, data: BasyxModels) -> DataModel:
        """
        Deserialize the specific format of the formater to a DataModel object.

        Args:
            data (Any): Basyx object store or Identifiable object

        Returns:
            DataModel: A data model that holds the types that were deserialized from the basyx template
        """
        if not isinstance(data, DictObjectStore):
            data = DictObjectStore(data)
        types = convert_object_store_to_pydantic_types(data)
        return DataModel.from_model_types(*types)


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

    def deserialize(
        self, data: BasyxModels, types: Optional[List[type[AAS | Submodel]]] = None
    ) -> DataModel:
        """
        Deserialize the specific format of the formater to a DataModel object.

        Args:
            data (Any): Basyx object store or Identifiable object

        Returns:
            DataModel: A data model that holds the objects that were deserialized
        """
        if not isinstance(data, DictObjectStore):
            data = DictObjectStore(data)
        models = convert_object_store_to_pydantic_models(data, types)
        return DataModel.from_models(*models)
