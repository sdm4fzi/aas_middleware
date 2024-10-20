import json
from typing import Dict, Union
from basyx.aas import model

import typing

from aas_middleware.model.formatting.aas import aas_model


def get_attribute_dict(
    obj: Union[aas_model.AAS, aas_model.Submodel, aas_model.SubmodelElementCollection]
) -> Dict[str, Union[aas_model.Submodel, aas_model.SubmodelElement]]:
    """
    Returns a dictionary of all attributes of an object that are not None, do not start with an underscore and are not standard attributes of the aas object.

    Args:
        obj (Union[aas_model.AAS, aas_model.Submodel, aas_model.SubmodelElementCollection]): Object to get the attributes from

    Returns:
        Dict[str, Union[aas_model.Submodel, aas_model.SubmodelElement]]: Dictionary of all attributes of the object and their respective values
    """
    vars_dict = vars(obj)
    vars_dict = {key: value for key, value in vars_dict.items() if key[0] != "_"}
    vars_dict = {key: value for key, value in vars_dict.items() if value is not None}
    vars_dict = {key: value for key, value in vars_dict.items() if key != "id"}
    vars_dict = {key: value for key, value in vars_dict.items() if key != "description"}
    vars_dict = {key: value for key, value in vars_dict.items() if key != "id_short"}
    vars_dict = {key: value for key, value in vars_dict.items() if key != "semantic_id"}
    return vars_dict


def get_str_description(langstring_set: model.LangStringSet) -> str:
    """
    Converts a LangStringSet to a string.
    Args:
        langstring_set (model.LangStringSet): LangStringSet to convert
    Returns:
        str: String representation of the LangStringSet
    """
    if not langstring_set:
        return ""
    dict_description = {}
    if "en" in langstring_set:
        return str(langstring_set.get("en"))
    elif "ger" in langstring_set:
        return str(langstring_set.get("ger"))
    elif "de" in langstring_set:
        return str(langstring_set.get("de"))
    else:
        return str(langstring_set.get(list(langstring_set.keys())[0]))


def get_basyx_description_from_model(
    model_object: (
        aas_model.AAS | aas_model.Submodel | aas_model.SubmodelElementCollection
    ),
) -> model.LangStringSet:
    """
    Creates a LangStringSet from an aas model.
    Args:
        model_object (aas_model.AAS | aas_model.Submodel | aas_model.SubmodelElementCollection): The model to get the description from.
    Returns:
        model.LangStringSet: LangStringSet description representation of the model object
    Raises:
        ValueError: If the description of the model object is not a dict or a string
    """
    if not model_object.description:
        return None
    try:
        dict_description = json.loads(model_object.description)
        if not isinstance(dict_description, dict):
            raise ValueError
    except ValueError:
        dict_description = {"en": model_object.description}
    return model.LangStringSet(dict_description)


def get_class_name_from_basyx_model(
    item: typing.Union[
        model.AssetAdministrationShell, model.Submodel, model.SubmodelElementCollection
    ]
) -> str:
    """
    Returns the class name of an basyx model from the data specifications.

    Args:
        item (model.HasDataSpecification): Basyx model to get the class name from

    Raises:
        ValueError: If no data specifications are found in the item or if no class name is found

    Returns:
        str: Class name of the basyx model
    """
    if not item.embedded_data_specifications:
        raise ValueError("No data specifications found in item:", item)
    for data_spec in item.embedded_data_specifications:
        content = data_spec.data_specification_content
        if not isinstance(content, model.DataSpecificationIEC61360):
            continue
        if not content.preferred_name.get("en") == "class":
            continue
        condition_smc = any(
            key.value == item.id_short for key in data_spec.data_specification.key
        )
        condition_aas_sm = hasattr(item, "id") and any(
            key.value == item.id for key in data_spec.data_specification.key
        )
        if not condition_smc and not condition_aas_sm:
            continue

        return content.value
    raise ValueError(
        f"No class name found in item with id {item.id_short} and type {type(item)}"
    )


def get_attribute_name_from_basyx_model(
    item: typing.Union[
        model.AssetAdministrationShell, model.Submodel, model.SubmodelElementCollection
    ],
    referenced_item_id: str,
) -> str:
    """
    Returns the attribute name of the referenced element of the item.

    Args:
        item (typing.Union[model.AssetAdministrationShell, model.Submodel, model.SubmodelElementCollection]): The container of the refernced item
        referenced_item_id (str): The id of the referenced item

    Raises:
        ValueError: If not data specifications are found in the item or if no attribute name is found

    Returns:
        str: The attribute name of the referenced item
    """
    if not item.embedded_data_specifications:
        raise ValueError("No data specifications found in item:", item)
    for data_spec in item.embedded_data_specifications:
        content = data_spec.data_specification_content
        if not isinstance(content, model.DataSpecificationIEC61360):
            continue
        if not any(
            key.value == referenced_item_id for key in data_spec.data_specification.key
        ):
            continue
        if not content.preferred_name.get("en") == "attribute":
            continue
        return content.value
    raise ValueError(
        f"Attribute reference to {referenced_item_id} could not be found in {item.id_short} of type {type(item)}"
    )


def is_attribute_from_basyx_model_immutable(
    item: typing.Union[
        model.AssetAdministrationShell, model.Submodel, model.SubmodelElementCollection
    ],
    referenced_item_id: str,
) -> bool:
    """
    Returns if the referenced item of the item is immutable.

    Args:
        item (typing.Union[model.AssetAdministrationShell, model.Submodel, model.SubmodelElementCollection]): The container of the refernced item
        referenced_item_id (str): The id of the referenced item

    Raises:
        ValueError: If not data specifications are found in the item or if no attribute name is found

    Returns:
        bool: If the referenced item is immutable
    """
    if not item.embedded_data_specifications:
        raise ValueError("No data specifications found in item:", item)
    for data_spec in item.embedded_data_specifications:
        content = data_spec.data_specification_content
        if not isinstance(content, model.DataSpecificationIEC61360):
            continue
        if not any(
            key.value == referenced_item_id for key in data_spec.data_specification.key
        ):
            continue
        if not content.preferred_name.get("en") == "immutable":
            continue
        return content.value == "true"
    raise ValueError(
        f"Attribute reference to {referenced_item_id} could not be found in {item.id_short} of type {type(item)}"
    )


def get_data_specification_for_model(
    item: typing.Union[
        aas_model.AAS, aas_model.Submodel, aas_model.SubmodelElementCollection
    ],
) -> typing.List[model.EmbeddedDataSpecification]:
    # TODO: maybe hide here the information if an attribute is optional or not
    return [model.EmbeddedDataSpecification(
        data_specification=model.ExternalReference(
            key=(
                model.Key(
                    type_=model.KeyTypes.GLOBAL_REFERENCE,
                    value=(
                        item.id
                        if isinstance(
                            item, typing.Union[aas_model.AAS, aas_model.Submodel]
                        )
                        else item.id_short
                    ),
                ),
            ),
        ),
        data_specification_content=model.DataSpecificationIEC61360(
            preferred_name=model.LangStringSet({"en": "class"}),
            value=item.__class__.__name__.split(".")[-1],
        ),
    )]


def get_data_specification_for_attribute(
    attribute_name: str, attribute_id: str, attribute_value: typing.Any
) -> typing.List[model.EmbeddedDataSpecification]:
    if isinstance(attribute_value, tuple):
        immutable = "true"
    else:
        immutable = "false"
    return [model.EmbeddedDataSpecification(
        data_specification=model.ExternalReference(
            key=(
                model.Key(
                    type_=model.KeyTypes.GLOBAL_REFERENCE,
                    value=attribute_id,
                ),
            ),
        ),
        data_specification_content=model.DataSpecificationIEC61360(
            preferred_name=model.LangStringSet({"en": "attribute"}),
            value=attribute_name,
        ),
    ),
    model.EmbeddedDataSpecification(
        data_specification=model.ExternalReference(
            key=(
                model.Key(
                    type_=model.KeyTypes.GLOBAL_REFERENCE,
                    value=attribute_id,
                ),
            ),
        ),
        data_specification_content=model.DataSpecificationIEC61360(
            preferred_name=model.LangStringSet({"en": "immutable"}),
            value=immutable,
        ),
    )
    
    
    
    ]


def get_id_short(
    element: Union[
        aas_model.AAS, aas_model.Submodel, aas_model.SubmodelElementCollection
    ]
) -> str:
    if element.id_short:
        return element.id_short
    else:
        return element.id


def get_semantic_id(
    model_object: aas_model.Submodel | aas_model.SubmodelElementCollection,
) -> str | None:
    if model_object.semantic_id:
        semantic_id = model.ExternalReference(
            key=(model.Key(model.KeyTypes.GLOBAL_REFERENCE, model_object.semantic_id),)
        )
    else:
        semantic_id = None
    return semantic_id


def get_value_type_of_attribute(
    attribute: Union[str, int, float, bool]
) -> model.datatypes:
    if isinstance(attribute, bool):
        return model.datatypes.Boolean
    elif isinstance(attribute, int):
        return model.datatypes.Integer
    elif isinstance(attribute, float):
        return model.datatypes.Double
    else:
        return model.datatypes.String


def get_semantic_id_value_of_model(
    basyx_model: typing.Union[model.Submodel, model.SubmodelElement]
) -> str:
    """
    Returns the semantic id of a submodel or submodel element.

    Args:
        basyx_model (model.Submodel | model.SubmodelElement): Basyx model to get the semantic id from.

    Returns:
        str: Semantic id of the model.
    """
    if not isinstance(basyx_model, model.HasSemantics):
        raise NotImplementedError("Type not implemented:", type(basyx_model))
    if not basyx_model.semantic_id:
        return ""
    return basyx_model.semantic_id.key[0].value
