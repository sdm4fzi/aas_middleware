from __future__ import annotations

import typing
from pydantic import create_model

from aas_middleware.model import core
from basyx.aas import model


from aas_middleware.model.formatting.aas_formatting import convert_util

def convert_object_store_to_pydantic_models(obj_store: model.DictObjectStore) -> typing.List[core.AAS]:
    """
    Converts an object store with AAS and submodels to pydantic models, representing the original data structure.

    Args:
        obj_store (model.DictObjectStore): Object store with AAS and submodels

    Returns:
        typing.List[core.AAS]: List of pydantic models
    """
    pydantic_submodels: typing.List[core.Submodel] = []
    for identifiable in obj_store:
        if isinstance(identifiable, model.Submodel):
            pydantic_submodel = convert_submodel_to_pydantic_model(identifiable)
            pydantic_submodels.append(pydantic_submodel)

    pydantic_aas_list: typing.List[core.AAS] = []
    for identifiable in obj_store:
        if isinstance(identifiable, model.AssetAdministrationShell):
            pydantic_aas = convert_aas_to_pydantic_model(identifiable, pydantic_submodels)
            pydantic_aas_list.append(pydantic_aas)

    return pydantic_aas_list

def convert_aas_to_pydantic_model(aas: model.AssetAdministrationShell, pydantic_submodels: typing.List[core.Submodel]) -> core.AAS:
    """
    Converts an AAS to a Pydantic model.

    Args:
        aas (model.AssetAdministrationShell): AAS to convert

    Returns:
        core.AAS: Pydantic model of the asset administration shell
    """
    # TODO: rework here if information in data specification changes
    aas_class_name = convert_util.get_class_name_from_basyx_model(aas)
    pydantic_core_aas = core.AAS(
        id=str(aas.id),
        id_short=aas.id_short,
        description=convert_util.get_str_description(aas.description),
    )
    dict_pydantic_core_aas = pydantic_core_aas.dict()
    aas_submodel_ids = [sm.get_identifier() for sm in aas.submodel]

    for counter, sm in enumerate(pydantic_submodels):
        class_name = type(sm).__name__
        if sm.id in aas_submodel_ids:
            attribute_name_of_submodel = convert_util.convert_camel_case_to_underscrore_str(class_name)
            dict_pydantic_core_aas.update({
                attribute_name_of_submodel: sm
                })
    model_type = create_model(aas_class_name, **dict_pydantic_core_aas, __core__=core.AAS)
    return model_type(**dict_pydantic_core_aas)


def convert_submodel_element_to_named_dict(sm_element: model.SubmodelElement) -> dict:
    """
    Converts a SubmodelElement to a dict.
    """
    if isinstance(sm_element, model.SubmodelElementCollection):
        attribute_value = convert_submodel_collection_to_pydantic_model(sm_element)
        attribute_name = convert_util.get_attribute_name_of_basyx_model(sm_element)
    elif isinstance(sm_element, model.SubmodelElementList):
        attribute_value = convert_submodel_list_to_pydantic_model(sm_element)
        attribute_name = convert_util.get_attribute_name_of_basyx_model(sm_element)
    elif isinstance(sm_element, model.ReferenceElement):
        attribute_value = convert_reference_element_to_pydantic_model(sm_element)
        attribute_name = convert_util.get_attribute_name_of_basyx_model(sm_element)
    elif isinstance(sm_element, model.Property):
        attribute_value = convert_property_to_pydantic_model(sm_element)
        attribute_name = convert_util.get_attribute_name_of_basyx_model(sm_element)
    else:
        raise NotImplementedError("Type not implemented:", type(sm_element))
    return {
        attribute_name: attribute_value
    }


def get_semantic_id_value_of_model(sm: typing.Union[model.Submodel, model.SubmodelElement]) -> str:
    """
    Returns the semantic id of a submodel or submodel element.
    """
    if isinstance(sm, model.Submodel):
        if not sm.semantic_id:
            return ""
        return sm.semantic_id.key[0].value
    elif isinstance(sm, model.SubmodelElement):
        if not sm.semantic_id:
            return ""
        return sm.semantic_id.key[0].value
    else:
        raise NotImplementedError("Type not implemented:", type(sm))
            
def convert_submodel_to_pydantic_model(sm: model.Submodel) -> core.Submodel:
    """
    Converts a Submodel to a Pydantic model.
    """
    class_name = convert_util.get_class_name_from_basyx_model(sm)
    pydantic_core_aas = core.Submodel(
        id=str(sm.id),
        id_short=sm.id_short,
        description=convert_util.get_str_description(sm.description),
        semantic_id=get_semantic_id_value_of_model(sm)
    )
    dict_pydantic_core_submodel = pydantic_core_aas.dict()
    for sm_element in sm.submodel_element:
        dict_sme = convert_submodel_element_to_named_dict(sm_element)
        dict_pydantic_core_submodel.update(dict_sme)
    model_type = create_model(class_name, **dict_pydantic_core_submodel, __core__=core.Submodel)
    return model_type(**dict_pydantic_core_submodel)


def convert_submodel_collection_to_pydantic_model(sm_element: model.SubmodelElementCollection) -> core.SubmodelElementCollection:
    """
    Converts a SubmodelElementCollection to a Pydantic model.
    """
    attribute_name = convert_util.get_attribute_name_of_basyx_model(sm_element)
    class_name = convert_util.convert_under_score_to_camel_case_str(attribute_name)
    sme_pydantic_model = core.SubmodelElementCollection(
        id_short=sm_element.id_short,
        description=convert_util.get_str_description(sm_element.description),
        semantic_id=get_semantic_id_value_of_model(sm_element)
    )
    dict_pydantic_core_submodel = sme_pydantic_model.dict()
    for sm_element in sm_element.value:
        dict_sme = convert_submodel_element_to_named_dict(sm_element)
        dict_pydantic_core_submodel.update(dict_sme)
    model_type = create_model(class_name, **dict_pydantic_core_submodel, __core__=core.SubmodelElementCollection)
    modelo = model_type(**dict_pydantic_core_submodel)
    return modelo

def convert_submodel_list_to_pydantic_model(sm_element: model.SubmodelElementList) -> typing.List[typing.Union[core.SubmodelElementCollection, str, int, float, bool, list, tuple, set]]:
    """
    Converts a SubmodelElementList to a Pydantic model.
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
    """
    return sm_element.value.key[0].value

def convert_property_to_pydantic_model(sm_element: model.Property) -> typing.Union[str, int, float, bool]:
    """
    Converts a Property to a Pydantic model.
    """
    return sm_element.value
