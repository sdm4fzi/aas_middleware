from typing import Any, Literal, Optional, Type, TypeVar, Union, List
import typing
from pydantic import BaseModel, Field, create_model

from aas_middleware.model.data_model import DataModel
from aas_middleware.model.formatting.aas import aas_model
from aas_middleware.model.reference_finder import ReferenceType
from aas_middleware.model.util import (
    get_id_with_patch,
    get_value_attributes,
    is_identifiable,
    is_identifiable_container,
)


def get_below_patch_type(patch_type: type) -> type:
    if patch_type == aas_model.AAS:
        return aas_model.Submodel
    elif patch_type == aas_model.Submodel:
        return aas_model.SubmodelElementCollection
    else:
        return aas_model.SubmodelElementCollection


T = TypeVar(
    "T", bound=aas_model.AAS | aas_model.Submodel | aas_model.SubmodelElementCollection
)


def get_type_hints_for_attribute(
    model: Any, attribute_name: str
) -> Type:
    if isinstance(model, BaseModel):
        return model.model_fields[attribute_name].annotation
    else:
        return typing.get_type_hints(model.__init__)[attribute_name]

def get_patched_type(
    model: Any, attribute_name: str, attribute_value: Any
) -> Type[T]:
    # TODO: this function should work without the specified attribute_value...
    attribute_type_hints = get_type_hints_for_attribute(model, attribute_name)
    if typing.get_origin(attribute_type_hints) == Union	and type(None) in typing.get_args(attribute_type_hints):
        return Optional[type(attribute_value)]
    elif typing.get_origin(attribute_type_hints) == Literal:
        return attribute_type_hints
    elif typing.get_origin(attribute_type_hints) == list:
        return List[type(attribute_value[0])]
    return type(attribute_value)


def get_patched_aas_object(model: Any, patch_type: Type[T]) -> T:
    """
    Rebuilds an Identifiable object to an AAS object.

    Args:
        model (object): The object to rebuild.

    Returns:
        aas_model.AAS: The rebuilt AAS object.
    """
    model_id = get_id_with_patch(model)
    dict_dynamic_model_creation = {}
    dict_model_instantiation = {}
    dict_model_instantiation["id_short"] = model_id
    if not patch_type == aas_model.SubmodelElementCollection:
        dict_model_instantiation["id"] = model_id

    for attribute_name, attribute_value in get_value_attributes(model).items():
        below_patch_type = get_below_patch_type(patch_type)

        if is_identifiable(attribute_value):
            patched_attribute_value = get_patched_aas_object(
                attribute_value, patch_type=below_patch_type
            )
        elif is_identifiable_container(attribute_value):
            patched_attribute_value = []
            for element in attribute_value:
                patched_element = get_patched_aas_object(
                    element, patch_type=below_patch_type
                )
                patched_attribute_value.append(patched_element)
        else:
            patched_attribute_value = attribute_value

        attribute_patch_type = get_patched_type(model, attribute_name, patched_attribute_value)

        dict_dynamic_model_creation.update(
            {
                attribute_name: (
                    attribute_patch_type,
                    Field(examples=[patched_attribute_value]),
                )
            }
        )
        dict_model_instantiation.update({attribute_name: patched_attribute_value})
    new_model_type = create_model(
        model.__class__.__name__, **dict_dynamic_model_creation, __base__=patch_type
    )
    return new_model_type.model_validate(dict_model_instantiation)


class DataModelRebuilder:
    def __init__(self, data_model: DataModel):
        """
        Rebuilds a data model with either direct or indirect references.

        Args:
            data_model (DataModel): The data model to rebuild.
        """
        self.data_model = data_model

    def rebuild_data_model_with_associations(self) -> DataModel:
        """
        Rebuilds all models in the data model with assosiations.

        Returns:
            DataModel: The rebuilt data model.
        """
        raise NotImplementedError

    def rebuild_data_model_for_AAS_structure(self) -> DataModel:
        """
        Rebuilds the data model for AAS meta model structure by adjusting the associations and references and infering correct AAS types.

        Returns:
            DataModel: The rebuilt data model.
        """
        aas_candidates = []
        submodel_candidates = []
        top_level_models_list = []
        for models in self.data_model.get_top_level_models().values():
            top_level_models_list += models

        for model in top_level_models_list:
            if isinstance(model, aas_model.AAS):
                aas_candidates.append(model)
                continue
            if any(
                reference_info.reference_type == ReferenceType.ASSOCIATION
                for reference_info in self.data_model.get_referencing_info(model)
            ):
                continue
            if not all(
                is_identifiable(attribute_value)
                for attribute_value in get_value_attributes(model).values()
            ):
                continue
            aas_candidates.append(model)

        for model in top_level_models_list:
            if model in aas_candidates:
                continue
            submodel_candidates.append(model)

        submodel_objects = []
        for submodel_candidate in submodel_candidates:
            # TODO: remove the need to patch models that are already subclasses of submodel...
            patched_submodel_object = get_patched_aas_object(
                submodel_candidate, patch_type=aas_model.Submodel
            )
            submodel_objects.append(patched_submodel_object)

        aas_objects = []
        for aas_candidate in aas_candidates:
            # TODO: remove the need to patch models that are already subclasses of aas...
            patched_aas_object = get_patched_aas_object(
                aas_candidate, patch_type=aas_model.AAS
            )
            aas_objects.append(patched_aas_object)

        aas_data_model = DataModel.from_models(*(aas_objects + submodel_objects))
        return aas_data_model

    def rebuild_data_model_with_references(self) -> DataModel:
        """
        Rebuilds all models in the data model with references.

        Returns:
            DataModel: The rebuilt data model.
        """
        raise NotImplementedError
