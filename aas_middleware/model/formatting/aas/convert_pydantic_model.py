from __future__ import annotations

from collections import OrderedDict
import json
import typing
from urllib import parse
from enum import Enum
import uuid


from basyx.aas import model

from typing import List, Optional, Tuple, Union
from pydantic import BaseModel, ConfigDict
from aas_middleware.model.data_model import DataModel
from aas_middleware.model.data_model_rebuilder import DataModelRebuilder
from aas_middleware.model.formatting.aas import convert_util, aas_model

from aas_middleware.model.formatting.aas.convert_util import (
    convert_primitive_type_to_xsdtype,
    get_attribute_infos,
    get_id_short,
    get_semantic_id,
    get_template_id,
    get_value_type_of_attribute,
)

import basyx.aas.adapter.json.json_serialization
import logging

logger = logging.getLogger(__name__)


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
    aas_attribute_infos = get_attribute_infos(model_aas)
    aas_submodels = {}
    aas_submodel_data_specifications = []
    for attribute_info in aas_attribute_infos:
        submodel = convert_model_to_submodel(model_submodel=attribute_info.value)
        attribute_data_specification = (
            convert_util.get_data_specification_for_attribute(attribute_info, submodel)
        )
        aas_submodel_data_specifications.append(attribute_data_specification)
        if submodel and not submodel.id_short in aas_submodels:
            aas_submodels.update({submodel.id_short: submodel})

    asset_information = model.AssetInformation(
        global_asset_id=model.Identifier(model_aas.id),
        asset_kind=model.AssetKind.INSTANCE,
        asset_type=model.Identifier("Instance"),
    )

    basyx_aas = model.AssetAdministrationShell(
        asset_information=asset_information,
        id_short=get_id_short(model_aas),
        id_=model.Identifier(model_aas.id),
        description=convert_util.get_basyx_description_from_model(model_aas),
        submodel={
            model.ModelReference.from_referable(submodel)
            for submodel in aas_submodels.values()
        },
        embedded_data_specifications=convert_util.get_data_specification_for_model(
            model_aas
        )
        + aas_submodel_data_specifications,
    )
    obj_store: model.DictObjectStore[model.Identifiable] = model.DictObjectStore()
    obj_store.add(basyx_aas)
    for sm in aas_submodels.values():
        obj_store.add(sm)
    return obj_store


def convert_model_to_submodel(
    model_submodel: aas_model.Submodel,
) -> Optional[model.Submodel]:
    if not model_submodel:
        return
    submodel_attributes = get_attribute_infos(model_submodel)
    submodel_elements = []
    submodel_element_data_specifications = []

    for attribute_info in submodel_attributes:
        submodel_element = create_submodel_element(
            attribute_info.name, attribute_info.value
        )
        attribute_data_specification = (
            convert_util.get_data_specification_for_attribute(
                attribute_info, submodel_element
            )
        )
        submodel_element_data_specifications.append(attribute_data_specification)
        immutable_attribute_data_specification = (
            convert_util.get_immutable_data_specification_for_attribute(attribute_info)
        )
        if immutable_attribute_data_specification:
            submodel_element_data_specifications.append(
                immutable_attribute_data_specification
            )
        if not attribute_info.field_info.is_required():
            default_data_specification = (
                convert_util.get_default_data_specification_for_attribute(
                    attribute_info, submodel_element
                )
            )
            submodel_element_data_specifications.append(default_data_specification)
        if submodel_element:
            submodel_elements.append(submodel_element)

    basyx_submodel = model.Submodel(
        id_short=get_id_short(model_submodel),
        id_=model.Identifier(model_submodel.id),
        description=convert_util.get_basyx_description_from_model(model_submodel),
        embedded_data_specifications=convert_util.get_data_specification_for_model(
            model_submodel
        )
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
) -> Optional[model.SubmodelElement]:
    """
    Create a basyx SubmodelElement from a model SubmodelElementCollection or a primitive type

    Args:
        attribute_name (str): Name of the attribute that is used for ID and id_short
        attribute_value (Union[ aas_model.SubmodelElementCollection, str, float, int, bool, tuple, list, set ]): Value of the attribute


    Returns:
        model.SubmodelElement: basyx SubmodelElement
    """
    if not attribute_value:
        return
    if isinstance(attribute_value, aas_model.SubmodelElementCollection):
        smc = create_submodel_element_collection(attribute_value)
        return smc
    elif isinstance(attribute_value, (list, tuple, set)):
        sml = create_submodel_element_list(attribute_name, attribute_value)
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
    elif isinstance(attribute_value, aas_model.File):
        return create_file(attribute_value)
    elif isinstance(attribute_value, aas_model.Blob):
        return create_blob(attribute_value)
    else:
        property = create_property(attribute_name, attribute_value)

        return property


def create_property(
    attribute_name: str,
    attribute_value: Union[str, int, float, bool],
) -> model.Property:
    if isinstance(attribute_value, Enum):
        attribute_value = attribute_value.value
        attribute_type = str
    else:
        attribute_type = type(attribute_value)

    property = model.Property(
        id_short=attribute_name,
        value_type=convert_primitive_type_to_xsdtype(attribute_type),
        value=attribute_value,
    )
    return property


def create_submodel_element_collection(
    model_sec: aas_model.SubmodelElementCollection,
) -> model.SubmodelElementCollection:
    value = []
    smc_attributes = get_attribute_infos(model_sec)
    submodel_element_data_specifications = []

    for attribute_info in smc_attributes:
        sme = create_submodel_element(attribute_info.name, attribute_info.value)
        attribute_data_specification = (
            convert_util.get_data_specification_for_attribute(attribute_info, sme)
        )
        submodel_element_data_specifications.append(attribute_data_specification)
        immutable_attribute_data_specification = (
            convert_util.get_immutable_data_specification_for_attribute(attribute_info)
        )
        if immutable_attribute_data_specification:
            submodel_element_data_specifications.append(
                immutable_attribute_data_specification
            )
        if not attribute_info.field_info.is_required():
            default_data_specification = (
                convert_util.get_default_data_specification_for_attribute(
                    attribute_info, sme
                )
            )
            submodel_element_data_specifications.append(default_data_specification)
        if sme:
            value.append(sme)

    id_short = get_id_short(model_sec)

    smc = model.SubmodelElementCollection(
        id_short=id_short,
        value=value,
        description=convert_util.get_basyx_description_from_model(model_sec),
        embedded_data_specifications=convert_util.get_data_specification_for_model(
            model_sec
        )
        + submodel_element_data_specifications,
        semantic_id=get_semantic_id(model_sec),
    )
    return smc


def patch_id_short_with_temp_attribute(
    submodel_element_collection: model.SubmodelElementCollection,
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
    attribute_name: str, value: list | tuple | set
) -> model.SubmodelElementList:
    submodel_elements = []
    submodel_element_ids = OrderedDict()
    for el in value:
        submodel_element = create_submodel_element(attribute_name, el)
        if isinstance(submodel_element, model.SubmodelElementCollection):
            if submodel_element.id_short in submodel_element_ids:
                raise ValueError(
                    f"Submodel element collection with id {submodel_element.id_short} already exists in list"
                )
            submodel_element_ids.update({submodel_element.id_short: None})
            patch_id_short_with_temp_attribute(submodel_element)
        submodel_element.id_short = None
        submodel_elements.append(submodel_element)

    if submodel_elements and isinstance(submodel_elements[0], model.Property):
        value_type_list_element = type(value.__iter__().__next__())
        type_value_list_element = type(submodel_elements[0])
    elif submodel_elements and isinstance(
        submodel_elements[0], model.Reference | model.SubmodelElementCollection
    ):
        value_type_list_element = None
        type_value_list_element = type(submodel_elements[0])
    else:
        value_type_list_element = convert_primitive_type_to_xsdtype(str)
        type_value_list_element = model.Property
    if isinstance(value, set):
        ordered = False
        iterable_type = "set"
    elif isinstance(value, tuple):
        ordered = True
        iterable_type = "tuple"
    elif isinstance(value, list):
        ordered = True
        iterable_type = "list"
    else:
        raise ValueError(
            f"Value must be a list, tuple or set, provided type {type(value)}"
        )

    sml = model.SubmodelElementList(
        id_short=f"{iterable_type}_{uuid.uuid4().hex}",
        type_value_list_element=type_value_list_element,
        value_type_list_element=value_type_list_element,
        value=submodel_elements,
        order_relevant=ordered,
    )
    return sml


def create_file(attribute_value: aas_model.File) -> model.File:
    """
    Function generates a basyx file objects from a pydantic File.

    Args:
        attribute_value (aas_model.File): pydantic File instance.

    Returns:
        model.File: Basyx file.
    """
    return model.File(
        id_short=attribute_value.id_short,
        description=attribute_value.description,
        semantic_id=attribute_value.semantic_id,
        content_type=attribute_value.media_type,
        value=attribute_value.path,
    )


def create_blob(attribute_value: aas_model.Blob) -> model.Blob:
    """
    Function generates a basyx file objects from a pydantic File.

    Args:
        attribute_value (aas_model.File): pydantic File instance.

    Returns:
        model.File: Basyx file.
    """
    return model.Blob(
        id_short=attribute_value.id_short,
        description=attribute_value.description,
        semantic_id=attribute_value.semantic_id,
        content_type=attribute_value.media_type,
        value=attribute_value.content,
    )
