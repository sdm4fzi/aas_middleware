from __future__ import annotations

import json
import typing
from urllib import parse
from enum import Enum
import uuid


from basyx.aas import model

from typing import Any, List, Optional, Set, Tuple, Union
from pydantic import BaseModel, ConfigDict
from aas_middleware.model.core import Reference
from aas_middleware.model.data_model import DataModel
from aas_middleware.model.data_model_rebuilder import DataModelRebuilder
from aas_middleware.model.formatting.aas import convert_util, aas_model

from aas_middleware.model.formatting.aas.convert_util import (
    get_attribute_field_infos,
    get_id_short,
    get_semantic_id,
    get_template_id,
    get_value_type_of_attribute,
)

import basyx.aas.adapter.json.json_serialization
import logging

logger = logging.getLogger(__name__)


def infere_aas_structure(
    data: DataModel,
) -> Tuple[List[aas_model.AAS], List[aas_model.Submodel]]:
    """
    The function assert that the data contained in the data model fulfills the aas meta model structure.

    Args:
        data (DataModel): The Data Model containing the objects that should be transformed to AAS models

    Returns:
        Tuple[List[aas_model.AAS], List[aas_model.Submodel]]: Tuple with AAS models and Submodel models
    """
    if all(all(isinstance(model, aas_model.AAS) for model in model_items) for model_items in data.get_top_level_models().values()):
        top_level_models_list = []
        for models in data.get_top_level_models().values():
            top_level_models_list += models
        return top_level_models_list, []
    logger.warning(
        "The data model does not contain only AAS models. Trying to infer the AAS structure by rebuilding the data model."
    )
    new_data_model = DataModelRebuilder(data).rebuild_data_model_for_AAS_structure()
    top_level_models_list = []
    for models in new_data_model.get_top_level_models().values():
        top_level_models_list += models
    aas_models = [
        model for model in top_level_models_list if isinstance(model, aas_model.AAS)
    ]
    submodel_models = [
        model
        for model in top_level_models_list
        if isinstance(model, aas_model.Submodel)
    ]
    return aas_models, submodel_models


def convert_model_to_aas_template(
    model_type: type[aas_model.AAS],
) -> model.DictObjectStore[model.Identifiable]:
    """
    Convert a model aas to an Basyx AssetAdministrationShell and return it as a DictObjectStore with all Submodels

    Args:
        model_type (type[aas_model.AAS]): Type of the model

    Returns:
        model.DictObjectStore[model.Identifiable]: DictObjectStore with all Submodels
    """
    aas_attribute_infos = get_attribute_field_infos(model_type)
    aas_submodels = []
    aas_submodel_data_specifications = []
    for attribute_info in aas_attribute_infos:
        submodel = convert_model_to_submodel_template(model_type=attribute_info.field_info.annotation)        
        attribute_data_specifications = convert_util.get_data_specification_for_attribute(
                attribute_info, submodel
        )
        aas_submodel_data_specifications += attribute_data_specifications
        if submodel:
            aas_submodels.append(submodel)


    asset_information = model.AssetInformation(
        asset_kind=model.AssetKind.TYPE,
        asset_type="Type",
        global_asset_id=model.Identifier(get_template_id(model_type)),
    )

    basyx_aas = model.AssetAdministrationShell(
        asset_information=asset_information,
        id_short=get_template_id(model_type),
        id_=model.Identifier(get_template_id(model_type)),
        description={"en": f"Type aas with id {get_template_id(model_type)} that contains submodel templates"},
        submodel={
            model.ModelReference.from_referable(submodel) for submodel in aas_submodels
        },
        embedded_data_specifications=convert_util.get_data_specification_for_model_template(model_type) + aas_submodel_data_specifications,
    )
    obj_store: model.DictObjectStore[model.Identifiable] = model.DictObjectStore()
    obj_store.add(basyx_aas)
    for sm in aas_submodels:
        obj_store.add(sm)
    return obj_store


def convert_model_to_submodel_template(
    model_type: type[aas_model.Submodel],
) -> Optional[model.Submodel]:
    if not model_type:
        return
    submodel_attributes = get_attribute_field_infos(model_type)
    submodel_elements = []
    submodel_element_data_specifications = []

    for attribute_info in submodel_attributes:
        submodel_element = create_submodel_element_template(
            attribute_info.name, attribute_info.field_info.annotation
        )
        attribute_data_specifications = convert_util.get_data_specification_for_attribute(
                attribute_info, submodel_element
        )
        submodel_element_data_specifications += attribute_data_specifications
        if submodel_element:
            submodel_elements.append(submodel_element)

    basyx_submodel = model.Submodel(
        id_short=get_template_id(model_type),
        id_=model.Identifier(get_template_id(model_type)),
        # descriptionconvert_util.get_basyx_description_from_model(model_type)=convert_util.get_basyx_description_from_model(model_type),
        description={"en": f"Submodel with id {get_template_id(model_type)} that contains submodel elements"},
        embedded_data_specifications=convert_util.get_data_specification_for_model_template(model_type)
        + submodel_element_data_specifications,
        semantic_id="",
        submodel_element=submodel_elements,
    )
    return basyx_submodel


def create_submodel_element_template(
    attribute_name: str,
    attribute_type: Union[
        type[aas_model.SubmodelElementCollection], type[str], type[float], type[int], type[bool], type[tuple], type[list], type[set]
    ],
) -> Optional[model.SubmodelElement]:
    """
    Create a basyx SubmodelElement from a model SubmodelElementCollection or a primitive type

    Args:
        attribute_name (str): Name of the attribute that is used for ID and id_short
        attribute_type (Union[type[aas_model.SubmodelElementCollection], type[str], type[float], type[int], type[bool], type[tuple], type[list], type[set]): Type of the attribute


    Returns:
        model.SubmodelElement: basyx SubmodelElement
    """
    if not attribute_type:
        return
    # FIXME: check how Union or Optional types can be handled...
    print(attribute_type)
    if typing.get_origin(attribute_type) == Optional:
        raise NotImplementedError(
            "Optional types are not supported for SubmodelElement creation"
        )
    if typing.get_origin(attribute_type) == Union:
        raise NotImplementedError(
            "Union types are not supported for SubmodelElement creation"
        )
    if typing.get_origin(attribute_type) == list:
        sml = create_submodel_element_list(attribute_name, attribute_type)
        return sml
    elif typing.get_origin(attribute_type) == tuple:
        sml = create_submodel_element_list(attribute_name, attribute_type)
        return sml
    elif typing.get_origin(attribute_type) == set:
        sml = create_submodel_element_list(
            attribute_name, attribute_type, ordered=False
        )
        return sml
    elif attribute_type == Reference:
        key = model.Key(
            type_=model.KeyTypes.ASSET_ADMINISTRATION_SHELL,
            value=get_template_id(attribute_type),
        )
        reference = model.ModelReference(key=(key,), type_="")
        reference_element = model.ReferenceElement(
            id_short=attribute_name,
            value=reference,
        )
        return reference_element
    elif issubclass(attribute_type, aas_model.SubmodelElementCollection):
        smc = create_submodel_element_collection(attribute_type)
        return smc
    else:
        property = create_property(attribute_name, attribute_type)

        return property


def create_property(
    attribute_name: str,
    attribute_type: Union[type[str], type[float], type[int], type[bool]],
) -> model.Property:
    if issubclass(attribute_type, Enum):
        attribute_type = str

    property = model.Property(
        id_short=attribute_name,
        value_type=attribute_type,
        value=None,
    )
    return property


def create_submodel_element_collection(
    model_sec: type[aas_model.SubmodelElementCollection],
) -> model.SubmodelElementCollection:
    value = []
    smc_attributes = get_attribute_field_infos(model_sec)
    submodel_element_data_specifications = []

    for attribute_info in smc_attributes:
        sme = create_submodel_element_template(attribute_info.name, attribute_info.field_info.annotation)
        attribute_data_specifications = (
            convert_util.get_data_specification_for_attribute(
                attribute_info, sme
            )
        )
        submodel_element_data_specifications += attribute_data_specifications
        if sme:
            value.append(sme)

    id_short = get_template_id(model_sec)

    smc = model.SubmodelElementCollection(
        id_short=id_short,
        value=value,
        # description=convert_util.get_basyx_description_from_model(model_sec),
        description={"en": f"Submodel element collection with id {id_short} that contains submodel elements"},
        embedded_data_specifications=convert_util.get_data_specification_for_model_template(model_sec) + submodel_element_data_specifications,
        semantic_id="",
    )
    return smc

def patch_id_short_with_temp_attribute(
        submodel_element_collection: model.SubmodelElementCollection
    ) -> None:
    """
    Patch the id_short of a SubmodelElementCollection as an attribute in the value of the SubmodelElementCollection, to make it accesible after retrieving from the value list.

    Args:
        submodel_element_collection (model.SubmodelElementCollection): SubmodelElementCollection to patch
    """
    temp_id_short_property = model.Property(
        id_short="temp_id_short_attribute_" + uuid.uuid4().hex,
        value_type=get_value_type_of_attribute(str),
        value=submodel_element_collection.id_short,
    )
    submodel_element_collection.value.add(temp_id_short_property)
        
        

    
def create_submodel_element_list(
    name: str, attribute_type: Union[type[tuple], type[list], type[set]],
    ordered=True
) -> model.SubmodelElementList:
    submodel_elements = []
    submodel_element_ids = set()
    for el in typing.get_args(attribute_type):
        submodel_element = create_submodel_element_template(name, el)
        if isinstance(submodel_element, model.SubmodelElementCollection):
            if submodel_element.id_short in submodel_element_ids:
                raise ValueError(
                    f"Submodel element collection with id {submodel_element.id_short} already exists in list"
                )
            submodel_element_ids.add(submodel_element.id_short)
            patch_id_short_with_temp_attribute(submodel_element)
        submodel_element.id_short = None
        submodel_elements.append(submodel_element)

    if submodel_elements and isinstance(submodel_elements[0], model.Property):
        if len(typing.get_args(attribute_type)) > 1:
            value_type_list_element = None
        else:
            value_type_list_element = submodel_elements[0].value_type
        type_value_list_element = type(submodel_elements[0])
    elif submodel_elements and isinstance(
        submodel_elements[0], model.Reference | model.SubmodelElementCollection | model.ReferenceElement | model.SubmodelElementList
    ):
        value_type_list_element = None
        type_value_list_element = type(submodel_elements[0])
    else:
        value_type_list_element = str
        type_value_list_element = model.Property

    # FIXME: resolve problem with SubmodelElementList that cannot take Enum values...
    # context=tuple([KPILevelEnum(context.value) for context in kpi.context]),
    # Update: should be resolved, needs to be tested here...
    sml = model.SubmodelElementList(
        id_short=name,
        type_value_list_element=type_value_list_element,
        value_type_list_element=value_type_list_element,
        value=submodel_elements,
        order_relevant=ordered,
    )
    return sml


class ClientModel(BaseModel):
    basyx_object: Union[model.AssetAdministrationShell, model.Submodel]

    model_config = ConfigDict(arbitrary_types_allowed=True)

    def to_dict(self) -> dict:
        basyx_json_string = json.dumps(
            self.basyx_object, cls=basyx.aas.adapter.json.AASToJsonEncoder
        )
        data: dict = json.loads(basyx_json_string)

        return data