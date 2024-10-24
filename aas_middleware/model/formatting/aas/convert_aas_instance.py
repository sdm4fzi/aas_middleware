from __future__ import annotations

import typing
from pydantic import BaseModel, TypeAdapter

from aas_middleware.model.formatting.aas import aas_model, convert_aas_template
from basyx.aas import model


from aas_middleware.model.formatting.aas import convert_util
from aas_middleware.model.formatting.aas.convert_aas import unpatch_id_short_from_temp_attribute
from aas_middleware.model.formatting.aas.convert_util import (
    is_attribute_from_basyx_model_immutable,
    get_semantic_id_value_of_model,
    repatch_id_short_to_temp_attribute,
)


def convert_object_store_to_pydantic_models(
    obj_store: model.DictObjectStore, types: typing.List[type] = None
) -> typing.List[aas_model.AAS]:
    """
    Converts an object store with AAS and submodels to pydantic models, representing the original data structure.

    Args:
        obj_store (model.DictObjectStore): Object store with AAS and submodels

    Returns:
        typing.List[aas_model.AAS]: List of pydantic models
    """
    type_name_dict = {t.__name__.split(".")[-1]: t for t in types}
    pydantic_submodels: typing.List[aas_model.Submodel] = []
    for identifiable in obj_store:
        if not isinstance(identifiable, model.Submodel):
            continue
        class_name = convert_util.get_class_name_from_basyx_model(identifiable)
        if not class_name in type_name_dict:
            # TODO: create here the types based on the submodel information and save them in the type_name_dict
            pass
        pydantic_submodel = convert_submodel_to_model_instance(identifiable, type_name_dict[class_name])
        pydantic_submodels.append(pydantic_submodel)

    pydantic_aas_list: typing.List[aas_model.AAS] = []
    for identifiable in obj_store:
        if not isinstance(identifiable, model.AssetAdministrationShell):
            continue
        class_name = convert_util.get_class_name_from_basyx_model(identifiable)
        if not class_name in type_name_dict:
            # TODO: create here the types based on the submodel information and save them in the type_name_dict
            pass
        pydantic_aas = convert_aas_to_pydantic_model_instance(
            identifiable, pydantic_submodels, type_name_dict[class_name]
        )
        pydantic_aas_list.append(pydantic_aas)

    return pydantic_aas_list


def convert_aas_to_pydantic_model_instance(
    aas: model.AssetAdministrationShell,
    pydantic_submodels: typing.List[aas_model.Submodel],
    model_type: type = aas_model.AAS,
) -> aas_model.AAS:
    """
    Converts an AAS to a Pydantic model.

    Args:
        aas (model.AssetAdministrationShell): AAS to convert

    Returns:
        aas_model.AAS: Pydantic model of the asset administration shell
    """
    dict_model_instantiation = get_initial_dict_for_model_instantiation(aas)
    aas_submodel_ids = [sm.get_identifier() for sm in aas.submodel]

    for sm in pydantic_submodels:
        if not sm.id in aas_submodel_ids:
            continue
        attribute_names_of_submodel = convert_util.get_attribute_names_from_basyx_template(
            aas, sm.id
        )
        if len(attribute_names_of_submodel) > 1:
            raise ValueError("Multiple attribute names found for submodel:", attribute_names_of_submodel)
        attribute_name_of_submodel = attribute_names_of_submodel[0]
        dict_model_instantiation.update({attribute_name_of_submodel: sm.model_dump()})
    return TypeAdapter(model_type).validate_python(dict_model_instantiation)


def get_submodel_element_value(
    sm_element: model.SubmodelElement, attribute_type: type = None
) -> aas_model.SubmodelElement:
    """
    Returns the value of a SubmodelElement.

    Args:
        sm_element (model.SubmodelElement): SubmodelElement to get the value from.

    Returns:
        aas_model.SubmodelElement: Value of the SubmodelElement.
    """
    if isinstance(sm_element, model.SubmodelElementCollection):
        return convert_submodel_collection_to_pydantic_model(sm_element, model_type=attribute_type)
    elif isinstance(sm_element, model.SubmodelElementList):
        return convert_submodel_list_to_pydantic_model(sm_element, model_type=attribute_type)
    elif isinstance(sm_element, model.ReferenceElement):
        return convert_reference_element_to_pydantic_model(sm_element)
    elif isinstance(sm_element, model.Property):
        return convert_property_to_pydantic_model(sm_element)
    else:
        raise NotImplementedError("Type not implemented:", type(sm_element))


def get_model_instantiation_dict_from_submodel_element(
    attribute_name: str, attribute_value: typing.Any
) -> typing.Dict[str, typing.Any]:
    """
    Converts a SubmodelElement to a dict.

    Args:
        attribute_name (str): Name of the attribute to create in the dictionary.
        sm_element (model.SubmodelElement): SubmodelElement to convert.

    Returns:
        dict: Dictionary that can be used to instantiate a Pydantic model.
    """
    if isinstance(attribute_value, BaseModel):
        attribute_value = attribute_value.model_dump()
    elif isinstance(attribute_value, (list, set, tuple)) and any(
        isinstance(element, BaseModel) for element in attribute_value
    ):
        attribute_value = [element.model_dump() for element in attribute_value]
    return {attribute_name: attribute_value}


def get_initial_dict_for_model_instantiation(
    basyx_model: (
        model.Submodel
        | model.AssetAdministrationShell
        | model.SubmodelElementCollection
    ),
) -> typing.Dict[str, typing.Any]:
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
        model_instantiation_dict["semantic_id"] = get_semantic_id_value_of_model(
            basyx_model
        )
    return model_instantiation_dict


def convert_submodel_to_model_instance(sm: model.Submodel, model_type: type[aas_model.Submodel] = None) -> aas_model.Submodel:
    """
    Converts a Submodel to a Pydantic model.

    Args:
        sm (model.Submodel): Submodel to convert.
        model_type (type[aas_model.Submodel]): Pydantic model type to convert the submodel to.

    Returns:
        aas_model.Submodel: Pydantic model of the submodel.
    """
    if model_type is None:
        model_type = convert_aas_template.convert_submodel_template_to_pydatic_type(
            sm
        )
    dict_model_instantiation = get_initial_dict_for_model_instantiation(sm)

    for sm_element in sm.submodel_element:
        attribute_names = convert_util.get_attribute_names_from_basyx_template(
            sm, sm_element.id_short
        )
        if len(attribute_names) > 1:
            raise ValueError("Multiple attribute names found for submodel element:", attribute_names)
        attribute_name = attribute_names[0]
        attribute_type = get_type_of_attribute(model_type, attribute_name)
        attribute_value = get_submodel_element_value(sm_element, attribute_type)
        sme_model_instantiation_dict = (
            get_model_instantiation_dict_from_submodel_element(
                attribute_name, attribute_value
            )
        )
        dict_model_instantiation.update(sme_model_instantiation_dict)
    return TypeAdapter(model_type).validate_python(dict_model_instantiation)


def get_type_of_attribute(model_type: typing.Union[type[BaseModel], typing.Union[type[BaseModel]]], attribute_name: str) -> typing.Union[type[BaseModel]]:
    """
    Returns the type of an attribute of a Pydantic model.

    Args:
        model_type (typing.Union[type[BaseModel], typing.Union]): Pydantic model type to get the attribute type from.
        attribute_name (str): Name of the attribute to get the type from.

    Returns:
        typing.Union[type[BaseModel], typing.Union]: Type of the attribute.
    """
    if typing.get_origin(model_type) is typing.Union:
        for contained_type in typing.get_args(model_type):
            if hasattr(contained_type, "model_fields") and attribute_name in contained_type.model_fields:
                return contained_type.model_fields[attribute_name].annotation
    if hasattr(model_type, "model_fields") and attribute_name in model_type.model_fields:
        return model_type.model_fields[attribute_name].annotation
    raise ValueError(f"Attribute {attribute_name} not found in model fields with attributes {list(model_type.model_fields.keys())}.")

def convert_submodel_collection_to_pydantic_model(
    sm_element: model.SubmodelElementCollection, model_type: type[aas_model.SubmodelElementCollection]
) -> aas_model.SubmodelElementCollection:
    """
    Converts a SubmodelElementCollection to a Pydantic model.

    Args:
        sm_element (model.SubmodelElementCollection): SubmodelElementCollection to convert.

    Returns:
        aas_model.SubmodelElementCollection: Pydantic model of the submodel element collection.
    """
    dict_model_instantiation = get_initial_dict_for_model_instantiation(sm_element)

    for sub_sm_element in sm_element.value:
        attribute_names = convert_util.get_attribute_names_from_basyx_template(
            sm_element, sub_sm_element.id_short
        )
        if len(attribute_names) > 1:
            raise ValueError("Multiple attribute names found for submodel element:", attribute_names)
        attribute_name = attribute_names[0]
        attribute_type = get_type_of_attribute(model_type, attribute_name)
        attribute_value = get_submodel_element_value(sub_sm_element, attribute_type)
        dict_sme_instantiation = get_model_instantiation_dict_from_submodel_element(
            attribute_name, attribute_value
        )
        dict_model_instantiation.update(dict_sme_instantiation)
    print("___new sec", sm_element.id_short, model_type)
    print(dict_model_instantiation)
    return TypeAdapter(model_type).validate_python(dict_model_instantiation)


def convert_submodel_list_to_pydantic_model(
    sm_element: model.SubmodelElementList, model_type: type[typing.Any]
) -> typing.Union[typing.List[aas_model.SubmodelElement], typing.Set[aas_model.SubmodelElement], typing.Tuple[aas_model.SubmodelElement]]:
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
            new_sme = unpatch_id_short_from_temp_attribute(sme)
            sme_pydantic_models.append(
                convert_submodel_collection_to_pydantic_model(new_sme, model_type=typing.get_args(model_type)[0])
            )
            repatch_id_short_to_temp_attribute(sme, new_sme)
        elif isinstance(sme, model.SubmodelElementList):
            sme_pydantic_models.append(convert_submodel_list_to_pydantic_model(sme, model_type=typing.get_args(model_type)[0]))
        elif isinstance(sme, model.ReferenceElement):
            sme_pydantic_models.append(convert_reference_element_to_pydantic_model(sme))
        elif isinstance(sme, model.Property):
            sme_pydantic_models.append(sme.value)
        else:
            raise NotImplementedError("Type not implemented:", type(sme))
    if not sm_element.order_relevant:
        return set(sme_pydantic_models)
    if model_type is tuple:
        return tuple(sme_pydantic_models)
    return sme_pydantic_models


def convert_reference_element_to_pydantic_model(
    sm_element: model.ReferenceElement,
) -> str:
    """
    Converts a ReferenceElement to a Pydantic model.

    Args:
        sm_element (model.ReferenceElement): ReferenceElement to convert.

    Returns:
        str: Value of the ReferenceElement.
    """
    return sm_element.value.key[0].value


def convert_property_to_pydantic_model(
    sm_element: model.Property,
) -> aas_model.PrimitiveSubmodelElement:
    """
    Converts a Property to a Pydantic model.

    Args:
        sm_element (model.Property): Property to convert.

    Returns:
        aas_model.PrimitiveSubmodelElement: Value of the Property.
    """
    return sm_element.value
