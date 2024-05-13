from __future__ import annotations

import typing
from attr import attrib
from pydantic import BaseModel, Field, create_model

from aas_middleware.model.formatting.aas import aas_model
from basyx.aas import model


from aas_middleware.model.formatting.aas import convert_util
from aas_middleware.model.formatting.aas.convert_util import get_semantic_id_value_of_model

def convert_object_store_to_pydantic_models(obj_store: model.DictObjectStore) -> typing.List[aas_model.AAS]:
    """
    Converts an object store with AAS and submodels to pydantic models, representing the original data structure.

    Args:
        obj_store (model.DictObjectStore): Object store with AAS and submodels

    Returns:
        typing.List[aas_model.AAS]: List of pydantic models
    """
    pydantic_submodels: typing.List[aas_model.Submodel] = []
    for identifiable in obj_store:
        if isinstance(identifiable, model.Submodel):
            pydantic_submodel = convert_submodel_to_pydantic_model(identifiable)
            pydantic_submodels.append(pydantic_submodel)

    pydantic_aas_list: typing.List[aas_model.AAS] = []
    for identifiable in obj_store:
        if isinstance(identifiable, model.AssetAdministrationShell):
            pydantic_aas = convert_aas_to_pydantic_model(identifiable, pydantic_submodels)
            pydantic_aas_list.append(pydantic_aas)

    return pydantic_aas_list

def convert_aas_to_pydantic_model(aas: model.AssetAdministrationShell, pydantic_submodels: typing.List[aas_model.Submodel]) -> aas_model.AAS:
    """
    Converts an AAS to a Pydantic model.

    Args:
        aas (model.AssetAdministrationShell): AAS to convert

    Returns:
        aas_model.AAS: Pydantic model of the asset administration shell
    """
    # TODO: rework here if information in data specification changes, also add that in data specifications the submodel attribute name is saved.
    aas_class_name = convert_util.get_class_name_from_basyx_model(aas)
    dict_dynamic_model_creation = get_initial_dict_for_dynamic_model_creation(aas)
    dict_model_instantiation = get_initial_dict_for_model_instantiation(aas)
    aas_submodel_ids = [sm.get_identifier() for sm in aas.submodel]

    for sm in pydantic_submodels:
        if not sm.id in aas_submodel_ids:
            continue
        attribute_name_of_submodel = convert_util.get_attribute_name_from_basyx_model(aas, sm.id)
        dict_dynamic_model_creation.update({
            attribute_name_of_submodel: typing.Annotated[type(sm), Field(examples=[sm])]
            })
        dict_model_instantiation.update({
            attribute_name_of_submodel: sm.model_dump()
            })
    model_type = create_model(aas_class_name, **dict_dynamic_model_creation, __base__=aas_model.AAS)
    return model_type(**dict_model_instantiation)


def get_submodel_element_value(sm_element: model.SubmodelElement) -> aas_model.SubmodelElement:
    """
    Returns the value of a SubmodelElement.

    Args:
        sm_element (model.SubmodelElement): SubmodelElement to get the value from.

    Returns:
        aas_model.SubmodelElement: Value of the SubmodelElement.
    """
    if isinstance(sm_element, model.SubmodelElementCollection):
        return convert_submodel_collection_to_pydantic_model(sm_element)
    elif isinstance(sm_element, model.SubmodelElementList):
        return convert_submodel_list_to_pydantic_model(sm_element)
    elif isinstance(sm_element, model.ReferenceElement):
        return convert_reference_element_to_pydantic_model(sm_element)
    elif isinstance(sm_element, model.Property):
        return convert_property_to_pydantic_model(sm_element)
    else:
        raise NotImplementedError("Type not implemented:", type(sm_element))


def get_dynamic_model_creation_dict_from_submodel_element(attribute_name: str, sm_element: model.SubmodelElement) -> typing.Dict[str, typing.Any]:
    """
    Converts a SubmodelElement to a dict.

    Args:
        attribute_name (str): Name of the attribute to create in the dictionary.
        sm_element (model.SubmodelElement): SubmodelElement to convert.

    Returns:
        dict: Dictionary that can be used to create a Pydantic model, with Annoated types for the attributes and examples.
    """
    attribute_value = get_submodel_element_value(sm_element)
    return {
        attribute_name: typing.Annotated[type(attribute_value), Field(examples=[attribute_value])]
    }

def get_model_instantiation_dict_from_submodel_element(attribute_name: str, sm_element: model.SubmodelElement) -> typing.Dict[str, typing.Any]:
    """
    Converts a SubmodelElement to a dict.

    Args:
        attribute_name (str): Name of the attribute to create in the dictionary.
        sm_element (model.SubmodelElement): SubmodelElement to convert.

    Returns:
        dict: Dictionary that can be used to instantiate a Pydantic model.
    """
    attribute_value = get_submodel_element_value(sm_element)
    if isinstance(attribute_value, BaseModel):
        attribute_value = attribute_value.model_dump()
    return {
        attribute_name: attribute_value
    }


def get_initial_dict_for_dynamic_model_creation(basyx_model: model.Submodel | model.AssetAdministrationShell | model.SubmodelElementCollection) -> typing.Dict[str, typing.Any]:
    """
    Returns a dictionary that can be used to create a Pydantic model based on a provided basyx submodel.

    Args:
        basyx_model (model.Submodel | model.AssetAdministrationShell | model.SubmodelElementCollection): Basyx model to create the dictionary from.

    Returns:
        typing.Dict[str, typing.Any]: Dictionary that can be used to create a Pydantic model.
    """
    model_creation_dict = {
        "id_short": typing.Annotated[str, Field(examples=[basyx_model.id_short])],
        "description": typing.Annotated[str, Field(examples=[convert_util.get_str_description(basyx_model.description)])],
    }
    if isinstance(basyx_model, model.Identifiable):
        model_creation_dict["id"] = typing.Annotated[str, Field(examples=[str(basyx_model.id)])]
    if isinstance(basyx_model, model.HasSemantics):
        model_creation_dict["semantic_id"] = typing.Annotated[str, Field(examples=[get_semantic_id_value_of_model(basyx_model)])]
    return model_creation_dict

def get_initial_dict_for_model_instantiation(basyx_model: model.Submodel | model.AssetAdministrationShell | model.SubmodelElementCollection) -> typing.Dict[str, typing.Any]:
    """
    Returns a dictionary that can be used to instantiate a Pydantic model based on a provided basyx submodel.

    Args:
        basyx_model (model.Submodel | model.AssetAdministrationShell | model.SubmodelElementCollection): Basyx model to create the dictionary from.

    Returns:
        typing.Dict[str, typing.Any]: Dictionary that can be used to instantiate a Pydantic model.
    """
    model_instantiation_dict = {
        "id_short": basyx_model.id_short,
        "description": convert_util.get_str_description(basyx_model.description),
    }
    if isinstance(basyx_model, model.Identifiable):
        model_instantiation_dict["id"] = str(basyx_model.id)
    if isinstance(basyx_model, model.HasSemantics):
        model_instantiation_dict["semantic_id"] = get_semantic_id_value_of_model(basyx_model)
    return model_instantiation_dict

            
def convert_submodel_to_pydantic_model(sm: model.Submodel) -> aas_model.Submodel:
    """
    Converts a Submodel to a Pydantic model.

    Args:
        sm (model.Submodel): Submodel to convert.

    Returns:
        aas_model.Submodel: Pydantic model of the submodel.
    """
    class_name = convert_util.get_class_name_from_basyx_model(sm)
    dict_dynamic_model_creation = get_initial_dict_for_dynamic_model_creation(sm)
    dict_model_instantiation = get_initial_dict_for_model_instantiation(sm)
    
    for sm_element in sm.submodel_element:
        # TODO: add possibility to specify the attribute name of properties in the data specification
        attribute_name = convert_util.get_attribute_name_from_basyx_model(sm, sm_element.id_short)
        sme_model_creation_dict = get_dynamic_model_creation_dict_from_submodel_element(attribute_name, sm_element)
        dict_dynamic_model_creation.update(sme_model_creation_dict)
        sme_model_instantiation_dict = get_model_instantiation_dict_from_submodel_element(attribute_name, sm_element)
        dict_model_instantiation.update(sme_model_instantiation_dict)
    model_type = create_model(class_name, **dict_dynamic_model_creation, __base__=aas_model.Submodel)
    return model_type(**dict_model_instantiation)


def convert_submodel_collection_to_pydantic_model(sm_element: model.SubmodelElementCollection) -> aas_model.SubmodelElementCollection:
    """
    Converts a SubmodelElementCollection to a Pydantic model.

    Args:
        sm_element (model.SubmodelElementCollection): SubmodelElementCollection to convert.

    Returns:
        aas_model.SubmodelElementCollection: Pydantic model of the submodel element collection.
    """
    class_name = convert_util.get_class_name_from_basyx_model(sm_element)
    dict_dynamic_model_creation = get_initial_dict_for_dynamic_model_creation(sm_element)
    dict_model_instantiation = get_initial_dict_for_model_instantiation(sm_element)

    for sub_sm_element in sm_element.value:
        attribute_name = convert_util.get_attribute_name_from_basyx_model(sm_element, sub_sm_element.id_short)
        dict_sme = get_dynamic_model_creation_dict_from_submodel_element(attribute_name, sub_sm_element)
        dict_dynamic_model_creation.update(dict_sme)
        dict_sme_instantiation = get_model_instantiation_dict_from_submodel_element(attribute_name, sub_sm_element)
        dict_model_instantiation.update(dict_sme_instantiation)
    model_type = create_model(class_name, **dict_dynamic_model_creation, __base__=aas_model.SubmodelElementCollection)
    return model_type(**dict_model_instantiation)

def convert_submodel_list_to_pydantic_model(sm_element: model.SubmodelElementList) -> typing.List[aas_model.SubmodelElement]:
    """
    Converts a SubmodelElementList to a Pydantic model.

    Args:
        sm_element (model.SubmodelElementList): SubmodelElementList to convert.

    Returns:
        typing.List[aas_model.SubmodelElement]: List of Pydantic models of the submodel elements.
    """
    sme_pydantic_models = []
    for sme in sm_element.value:
        if isinstance(sme, model.SubmodelElementCollection):
            sme_pydantic_models.append(convert_submodel_collection_to_pydantic_model(sme))
        elif isinstance(sme, model.SubmodelElementList):
            sme_pydantic_models.append(convert_submodel_list_to_pydantic_model(sme))
        elif isinstance(sme, model.ReferenceElement):
            sme_pydantic_models.append(convert_reference_element_to_pydantic_model(sme))
        elif isinstance(sme, model.Property):
            sme_pydantic_models.append(sme.value)
        else:
            raise NotImplementedError("Type not implemented:", type(sme))
    return sme_pydantic_models

def convert_reference_element_to_pydantic_model(sm_element: model.ReferenceElement) -> str:
    """
    Converts a ReferenceElement to a Pydantic model.

    Args:
        sm_element (model.ReferenceElement): ReferenceElement to convert.

    Returns:
        str: Value of the ReferenceElement.
    """
    return sm_element.value.key[0].value

def convert_property_to_pydantic_model(sm_element: model.Property) -> aas_model.PrimitiveSubmodelElement:
    """
    Converts a Property to a Pydantic model.

    Args:
        sm_element (model.Property): Property to convert.

    Returns:
        aas_model.PrimitiveSubmodelElement: Value of the Property.
    """
    return sm_element.value
