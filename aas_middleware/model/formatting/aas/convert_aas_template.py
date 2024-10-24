from __future__ import annotations

import logging
import typing
from pydantic import BaseModel, Field, create_model
from pydantic_core import PydanticUndefined

from aas_middleware.model.core import Reference
from aas_middleware.model.formatting.aas import aas_model
from basyx.aas import model


from aas_middleware.model.formatting.aas import convert_util
from aas_middleware.model.formatting.aas.convert_util import (
    convert_xsdtype_to_primitive_type,
    get_semantic_id_value_of_model,
    repatch_id_short_to_temp_attribute,
    unpatch_id_short_from_temp_attribute,
)


def convert_object_store_to_pydantic_types(
    obj_store: model.DictObjectStore,
) -> typing.List[type[aas_model.AAS]]:
    """
    Converts an object store with AAS and submodels to pydantic models, representing the original data structure.

    Args:
        obj_store (model.DictObjectStore): Object store with AAS and submodels

    Returns:
        typing.List[aas_model.AAS]: List of pydantic models
    """
    pydantic_submodel_types: typing.List[aas_model.Submodel] = []
    submodels_pydantic_type_mapping = {}
    for identifiable in obj_store:
        if isinstance(identifiable, model.Submodel):
            pydantic_submodel = convert_submodel_template_to_pydatic_type(identifiable)
            pydantic_submodel_types.append(pydantic_submodel)
            submodels_pydantic_type_mapping[identifiable.id] = (pydantic_submodel, identifiable)

    pydantic_aas_list: typing.List[type[aas_model.AAS]] = []
    for identifiable in obj_store:
        if isinstance(identifiable, model.AssetAdministrationShell):
            pydantic_aas = convert_aas_to_pydantic_type(
                identifiable, submodels_pydantic_type_mapping
            )
            pydantic_aas_list.append(pydantic_aas)

    return pydantic_aas_list


def convert_aas_to_pydantic_type(
    aas: model.AssetAdministrationShell,
    pydantic_submodel_types: typing.Dict[str, typing.Tuple[type[aas_model.Submodel], model.Submodel]],
) -> type[aas_model.AAS]:
    """
    Converts an AAS to a Pydantic model.

    Args:
        aas (model.AssetAdministrationShell): AAS to convert

    Returns:
        aas_model.AAS: Pydantic model of the asset administration shell
    """
    aas_class_name = convert_util.get_class_name_from_basyx_template(aas)
    dict_dynamic_model_creation = get_initial_dict_for_dynamic_model_creation(aas)
    aas_submodel_ids = [sm.get_identifier() for sm in aas.submodel]

    for submodel_id in aas_submodel_ids:
        pydantic_submodel_type, basyx_submodel = pydantic_submodel_types[submodel_id]
        attribute_names_of_submodel = convert_util.get_attribute_names_from_basyx_template(
            aas, basyx_submodel.id_short
        )
        for attribute_name in attribute_names_of_submodel:
            optional = convert_util.is_optional_attribute_type(aas, attribute_name)
            union = convert_util.is_union_attribute_type(aas, attribute_name)
            if optional:
                pydantic_submodel_type = typing.Optional[pydantic_submodel_type]
            if pydantic_submodel_type is None:
                logging.warning(
                    f"Could not convert submodel {submodel_id} to Pydantic model. Skipping."
                )
                continue
            if union and attribute_name in dict_dynamic_model_creation:
                pydantic_submodel_type = typing.Union[
                    dict_dynamic_model_creation[attribute_name], pydantic_submodel_type
                ]
            dict_dynamic_model_creation.update(
                {
                    attribute_name: typing.Annotated[
                        pydantic_submodel_type, Field(examples=[])
                    ]
                }
            )
    model_type = create_model(
        aas_class_name, **dict_dynamic_model_creation, __base__=aas_model.AAS
    )
    return model_type

def get_submodel_element_type(
    sm_element: model.SubmodelElement, immutable: bool = False
) -> type[aas_model.SubmodelElement]:
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
        return convert_submodel_list_to_pydantic_model(sm_element, immutable)
    elif isinstance(sm_element, model.ReferenceElement):
        return convert_reference_element_to_pydantic_model(sm_element)
    elif isinstance(sm_element, model.RelationshipElement):
        return convert_relationship_element_to_pydantic_model(sm_element)
    elif isinstance(sm_element, model.Property):
        return convert_property_to_pydantic_model(sm_element)
    elif isinstance(sm_element, model.MultiLanguageProperty):
        return convert_multi_language_property_to_pydantic_model(sm_element)
    elif isinstance(sm_element, model.File):
        # TODO: handle files in the future
        print(f"file with id {sm_element.id_short} and value: {sm_element.value}")
    elif isinstance(sm_element, model.Blob):
        # TODO: handle blobs in the future
        print(f"blob with id {sm_element.id_short} and value: {sm_element.value}")
    else:
        raise NotImplementedError("Type not implemented:", type(sm_element))


def get_dynamic_model_creation_dict_from_submodel_element(
    attribute_name: str, attribute_type: typing.Type[typing.Any], default_value: typing.Any = None
) -> typing.Dict[str, typing.Any]:
    """
    Converts a SubmodelElement to a dict.

    Args:
        attribute_name (str): Name of the attribute to create in the dictionary.
        sm_element (model.SubmodelElement): SubmodelElement to convert.

    Returns:
        dict: Dictionary that can be used to create a Pydantic model, with Annoated types for the attributes and examples.
    """
    if not default_value:
        default_value = PydanticUndefined
    return {
        attribute_name: typing.Annotated[
            attribute_type, Field(examples=[], default=default_value)
        ]
    }


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


def get_initial_dict_for_dynamic_model_creation(
    basyx_model: (
        model.Submodel
        | model.AssetAdministrationShell
        | model.SubmodelElementCollection
    ),
) -> typing.Dict[str, typing.Any]:
    """
    Returns a dictionary that can be used to create a Pydantic model based on a provided basyx submodel.

    Args:
        basyx_model (model.Submodel | model.AssetAdministrationShell | model.SubmodelElementCollection): Basyx model to create the dictionary from.

    Returns:
        typing.Dict[str, typing.Any]: Dictionary that can be used to create a Pydantic model.
    """
    # model_creation_dict = {
    #     "id_short": typing.Annotated[str, Field(examples=[basyx_model.id_short])],
    #     "description": typing.Annotated[
    #         str,
    #         Field(examples=[convert_util.get_str_description(basyx_model.description)]),
    #     ],
    # }
    # if isinstance(basyx_model, model.Identifiable):
    #     model_creation_dict["id"] = typing.Annotated[
    #         str, Field(examples=[str(basyx_model.id)])
    #     ]
    # if isinstance(basyx_model, model.HasSemantics):
    #     model_creation_dict["semantic_id"] = typing.Annotated[
    #         str, Field(examples=[get_semantic_id_value_of_model(basyx_model)])
    #     ]
    # return model_creation_dict
    return {}

def convert_submodel_template_to_pydatic_type(sm: model.Submodel) -> type[aas_model.Submodel]:
    """
    Converts a Submodel to a Pydantic model.

    Args:
        sm (model.Submodel): Submodel to convert.

    Returns:
        aas_model.Submodel: Pydantic model of the submodel.
    """
    class_name = convert_util.get_class_name_from_basyx_template(sm)
    dict_dynamic_model_creation = get_initial_dict_for_dynamic_model_creation(sm)

    for sm_element in sm.submodel_element:
        attribute_names = convert_util.get_attribute_names_from_basyx_template(
            sm, sm_element.id_short
        )
        for attribute_name in attribute_names:
            optional = convert_util.is_optional_attribute_type(sm, attribute_name)
            union = convert_util.is_union_attribute_type(sm, attribute_name)
            immutable = convert_util.is_attribute_from_basyx_model_immutable(sm, attribute_name)
            default_value = convert_util.get_default_value_from_basyx_model(sm, sm_element.id_short)
            attribute_type = get_submodel_element_type(sm_element, immutable)

            if optional:
                attribute_type = typing.Optional[attribute_type]
            if attribute_type is None:
                logging.warning(
                    f"Could not convert submodel element {attribute_name} to Pydantic model. Skipping."
                )
                continue
            if union and attribute_name in dict_dynamic_model_creation:
                attribute_type  = typing.Union[
                    dict_dynamic_model_creation[attribute_name], attribute_type
                ]
            sme_model_creation_dict = get_dynamic_model_creation_dict_from_submodel_element(
                attribute_name, attribute_type, default_value
            )
            dict_dynamic_model_creation.update(sme_model_creation_dict)
    model_type = create_model(
        class_name, **dict_dynamic_model_creation, __base__=aas_model.Submodel
    )
    return model_type


def convert_submodel_collection_to_pydantic_model(
    sm_element: model.SubmodelElementCollection,
) -> type[aas_model.SubmodelElementCollection]:
    """
    Converts a SubmodelElementCollection to a Pydantic model.

    Args:
        sm_element (model.SubmodelElementCollection): SubmodelElementCollection to convert.

    Returns:
        aas_model.SubmodelElementCollection: Pydantic model of the submodel element collection.
    """
    class_name = convert_util.get_class_name_from_basyx_template(sm_element)
    dict_dynamic_model_creation = get_initial_dict_for_dynamic_model_creation(
        sm_element
    )

    for sub_sm_element in sm_element.value:
        attribute_names = convert_util.get_attribute_names_from_basyx_template(
            sm_element, sub_sm_element.id_short
        )
        for attribute_name in attribute_names:
            optional = convert_util.is_optional_attribute_type(sm_element, attribute_name)
            union = convert_util.is_union_attribute_type(sm_element, attribute_name)
            immutable = convert_util.is_attribute_from_basyx_model_immutable(sm_element, attribute_name)
            default_value = convert_util.get_default_value_from_basyx_model(sm_element, sub_sm_element.id_short)
            attribute_type = get_submodel_element_type(sub_sm_element, immutable)

            if optional:
                attribute_type = typing.Optional[attribute_type]
            if attribute_type is None:
                logging.warning(
                    f"Could not convert submodel element {attribute_name} to Pydantic model. Skipping."
                )
                continue
            if union and attribute_name in dict_dynamic_model_creation:
                attribute_type  = typing.Union[
                    dict_dynamic_model_creation[attribute_name], attribute_type
                ] 
            dict_sme = get_dynamic_model_creation_dict_from_submodel_element(
                attribute_name, attribute_type, default_value
            )
            dict_dynamic_model_creation.update(dict_sme)
    model_type = create_model(
        class_name,
        **dict_dynamic_model_creation,
        __base__=aas_model.SubmodelElementCollection,
    )
    return model_type


def convert_submodel_list_to_pydantic_model(
    sm_element: model.SubmodelElementList, immutable: bool = False
) -> type[typing.Union[typing.List[aas_model.SubmodelElement], typing.Set[aas_model.SubmodelElement]]]:
    """
    Converts a SubmodelElementList to a Pydantic model.

    Args:
        sm_element (model.SubmodelElementList): SubmodelElementList to convert.

    Returns:
        typing.List[aas_model.SubmodelElement]: List of Pydantic models of the submodel elements.
    """
    if sm_element.value_type_list_element is not None:
        value_type = convert_xsdtype_to_primitive_type(sm_element.value_type_list_element)
    else:
        sm_element_value = sm_element.value[0]
        if isinstance(sm_element_value, model.SubmodelElementCollection):
            new_sm_element_value = unpatch_id_short_from_temp_attribute(sm_element_value)
            value_type = convert_submodel_collection_to_pydantic_model(new_sm_element_value)
            repatch_id_short_to_temp_attribute(sm_element_value, new_sm_element_value)

        elif isinstance(sm_element_value, model.SubmodelElementList):
            value_type = convert_submodel_list_to_pydantic_model(sm_element_value)
        elif isinstance(sm_element_value, model.ReferenceElement):
            value_type = convert_reference_element_to_pydantic_model(sm_element_value)
        elif isinstance(sm_element_value, model.RelationshipElement):
            value_type = convert_relationship_element_to_pydantic_model(sm_element_value)
        elif isinstance(sm_element_value, model.Property):
            value_type = convert_property_to_pydantic_model(sm_element_value)
        else:
            raise NotImplementedError("Type not implemented:", type(sm_element_value))
    if immutable:
        return typing.Tuple[value_type, ...]
    if not sm_element.order_relevant:
        return typing.Set[value_type]
    return typing.List[value_type]


def convert_reference_element_to_pydantic_model(
    sm_element: model.ReferenceElement,
) -> type[Reference]:
    """
    Converts a ReferenceElement to a Pydantic model.

    Args:
        sm_element (model.ReferenceElement): ReferenceElement to convert.

    Returns:
        str: Value of the ReferenceElement.
    """
    return Reference


def convert_relationship_element_to_pydantic_model(
    sm_element: model.RelationshipElement,
) -> type[typing.Tuple[Reference, Reference]]:
    """
    Converts a RelationshipElement to a Pydantic model.
    """
    return typing.Tuple[Reference, Reference]

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
    return convert_xsdtype_to_primitive_type(sm_element.value_type)


def convert_multi_language_property_to_pydantic_model(
    sm_element: model.MultiLanguageProperty,
) -> aas_model.PrimitiveSubmodelElement:
    """
    Converts a MultiLanguageProperty to a Pydantic model.

    Args:
        sm_element (model.MultiLanguageProperty): MultiLanguageProperty to convert.

    Returns:
        aas_model.PrimitiveSubmodelElement: Value of the MultiLanguageProperty.
    """
    return str