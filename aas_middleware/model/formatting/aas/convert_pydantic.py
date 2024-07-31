from __future__ import annotations

import json
from urllib import parse
from enum import Enum
import uuid


from basyx.aas import model

from typing import List, Tuple, Union
from pydantic import BaseModel, ConfigDict
from aas_middleware.model.data_model import DataModel
from aas_middleware.model.data_model_rebuilder import DataModelRebuilder
from aas_middleware.model.formatting.aas import convert_util, aas_model

from aas_middleware.model.formatting.aas.convert_util import (
    get_attribute_dict,
    get_id_short,
    get_semantic_id,
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


def convert_model_to_aas(
    model_aas: aas_model.AAS,
) -> model.DictObjectStore[model.Identifiable]:
    """
    Convert a model aas to an Basyx AssetAdministrationShell and return it as a DictObjectStore with all Submodels

    Args:
        model_aas (aas_model.AAS): model aas to convert

    Returns:
        model.DictObjectStore[model.Identifiable]: DictObjectStore with all Submodels
    """
    aas_attributes = get_attribute_dict(model_aas)
    aas_submodels = []  # placeholder for submodels created
    aas_submodel_data_specifications = []
    for attribute_name, attribute_value in aas_attributes.items():
        if isinstance(attribute_value, aas_model.Submodel):
            tempsubmodel = convert_model_to_submodel(model_submodel=attribute_value)
            aas_submodels.append(tempsubmodel)
            attribute_data_specifications = convert_util.get_data_specification_for_attribute(
                    attribute_name, attribute_value.id, attribute_value
                
            )
            aas_submodel_data_specifications += attribute_data_specifications

    asset_information = model.AssetInformation(
        global_asset_id=model.Identifier(model_aas.id),
    )

    basyx_aas = model.AssetAdministrationShell(
        asset_information=asset_information,
        id_short=get_id_short(model_aas),
        id_=model.Identifier(model_aas.id),
        description=convert_util.get_basyx_description_from_model(model_aas),
        submodel={
            model.ModelReference.from_referable(submodel) for submodel in aas_submodels
        },
        embedded_data_specifications=convert_util.get_data_specification_for_model(model_aas) + aas_submodel_data_specifications,
    )
    obj_store: model.DictObjectStore[model.Identifiable] = model.DictObjectStore()
    obj_store.add(basyx_aas)
    for sm in aas_submodels:
        obj_store.add(sm)
    return obj_store


def convert_model_to_submodel(
    model_submodel: aas_model.Submodel,
) -> model.Submodel:
    submodel_attributes = get_attribute_dict(model_submodel)
    submodel_elements = []
    submodel_element_data_specifications = []

    for sm_attribute_name, sm_attribute_value in submodel_attributes.items():
        submodel_element = create_submodel_element(
            sm_attribute_name, sm_attribute_value
        )
        submodel_elements.append(submodel_element)
        attribute_data_specifications = convert_util.get_data_specification_for_attribute(
                sm_attribute_name, submodel_element.id_short, sm_attribute_value
            )
        submodel_element_data_specifications += attribute_data_specifications

    basyx_submodel = model.Submodel(
        id_short=get_id_short(model_submodel),
        id_=model.Identifier(model_submodel.id),
        description=convert_util.get_basyx_description_from_model(model_submodel),
        embedded_data_specifications=convert_util.get_data_specification_for_model(model_submodel)
        + submodel_element_data_specifications,
        semantic_id=get_semantic_id(model_submodel),
        submodel_element=submodel_elements,
    )
    return basyx_submodel


def create_submodel_element(
    attribute_name: str,
    attribute_value: Union[
        aas_model.SubmodelElementCollection, str, float, int, bool, tuple, list, set
    ],
) -> model.SubmodelElement:
    """
    Create a basyx SubmodelElement from a model SubmodelElementCollection or a primitive type

    Args:
        attribute_name (str): Name of the attribute that is used for ID and id_short
        attribute_value (Union[ aas_model.SubmodelElementCollection, str, float, int, bool, tuple, list, set ]): Value of the attribute


    Returns:
        model.SubmodelElement: basyx SubmodelElement
    """
    if isinstance(attribute_value, aas_model.SubmodelElementCollection):
        smc = create_submodel_element_collection(attribute_value)
        return smc
    elif isinstance(attribute_value, list):
        sml = create_submodel_element_list(attribute_name, attribute_value)
        return sml
    elif isinstance(attribute_value, tuple):
        attribute_value_as_list = list(attribute_value)
        sml = create_submodel_element_list(attribute_name, attribute_value_as_list)
        return sml
    elif isinstance(attribute_value, set):
        attribute_value_as_list = list(attribute_value)	
        sml = create_submodel_element_list(
            attribute_name, attribute_value_as_list, ordered=False
        )
        return sml
    elif (isinstance(attribute_value, str)) and (
        (
            parse.urlparse(attribute_value).scheme
            and parse.urlparse(attribute_value).netloc
        )
        or (attribute_value.split("_")[-1] in ["id", "ids"])
    ):
        key = model.Key(
            type_=model.KeyTypes.ASSET_ADMINISTRATION_SHELL,
            value=attribute_value,
        )
        reference = model.ModelReference(key=(key,), type_="")
        reference_element = model.ReferenceElement(
            id_short=attribute_name,
            value=reference,
        )
        return reference_element
    else:
        property = create_property(attribute_name, attribute_value)

        return property


def create_property(
    attribute_name: str,
    attribute_value: Union[str, int, float, bool],
) -> model.Property:
    if isinstance(attribute_value, Enum):
        attribute_value = attribute_value.value

    property = model.Property(
        id_short=attribute_name,
        value_type=get_value_type_of_attribute(attribute_value),
        value=attribute_value,
    )
    return property


def create_submodel_element_collection(
    model_sec: aas_model.SubmodelElementCollection,
) -> model.SubmodelElementCollection:
    value = []
    smc_attributes = get_attribute_dict(model_sec)
    submodel_element_data_specifications = []

    for attribute_name, attribute_value in smc_attributes.items():
        sme = create_submodel_element(attribute_name, attribute_value)
        value.append(sme)
        attribute_data_specifications = (
            convert_util.get_data_specification_for_attribute(
                attribute_name, sme.id_short, model_sec
            )
        )
        submodel_element_data_specifications += attribute_data_specifications

    id_short = get_id_short(model_sec)

    smc = model.SubmodelElementCollection(
        id_short=id_short,
        value=value,
        description=convert_util.get_basyx_description_from_model(model_sec),
        embedded_data_specifications=convert_util.get_data_specification_for_model(model_sec) + submodel_element_data_specifications,
        semantic_id=get_semantic_id(model_sec),
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
    name: str, value: list | tuple | set, ordered=True
) -> model.SubmodelElementList:
    submodel_elements = []
    submodel_element_ids = set()
    for el in value:
        submodel_element = create_submodel_element(name, el)
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
        value_type_list_element = type(value[0])
        type_value_list_element = type(submodel_elements[0])
    elif submodel_elements and isinstance(
        submodel_elements[0], model.Reference | model.SubmodelElementCollection
    ):
        value_type_list_element = None
        type_value_list_element = type(submodel_elements[0])
    else:
        value_type_list_element = str
        type_value_list_element = model.Property

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
