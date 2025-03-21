from __future__ import annotations
import inspect
import re
from types import NoneType
from typing import Any, Dict, List, Set, Optional, Tuple, Type, Union
import typing
from uuid import UUID

from pydantic import BaseModel
from pydantic.fields import FieldInfo

from aas_middleware.model.core import (
    Identifiable,
    Identifier,
    Reference,
    UnIdentifiable,
)


def convert_camel_case_to_underscrore_str(came_case_string: str) -> str:
    """
    Convert a camel case string to an underscore seperated string.

    Args:
        class_name (str): The camel case string to convert.

    Returns:
        str: The underscore seperated string.
    """
    came_case_string = came_case_string[0].lower() + came_case_string[1:]
    new_class_name = re.sub(r"(?<!^)(?=[A-Z])", "_", came_case_string).lower()
    if all(len(el) == 1 for el in new_class_name.split("_")):
        new_class_name = new_class_name.replace("_", "")
    return new_class_name


def convert_under_score_to_camel_case_str(underscore_str: str) -> str:
    """
    Convert a underscore seperated string to a camel case string.

    Args:
        class_name (str): The underscore seperated string to convert.

    Returns:
        str: The camel case string.
    """
    words = underscore_str.split("_")
    camel_case_str = "".join(word[0].capitalize() + word[1:] for word in words)
    return camel_case_str


def is_identifiable(model: Any) -> bool:
    """
    Function to check if a model is identifiable.

    Args:
        model (Any): The model.

    Returns:
        bool: True if the model is identifiable, False otherwise.
    """
    return not isinstance(model, UnIdentifiable)


def get_identifier_type_fields(field_info_dict: Dict[str, FieldInfo]) -> List[str]:
    """
    Function to get the fields of a model that are of type Identifier.

    Args:
        model (BaseModel): A Basemodel that is checked for identifier fields

    Returns:
        List[str]: The field names that are Identifiers
    """
    model_fields = []
    for field_name, field_info in field_info_dict.items():
        if field_info.annotation == Identifier:
            model_fields.append(field_name)
    return model_fields


def get_id(model: Any) -> str | int | UUID:
    """
    Function to get the id attribute of an arbitrary model.

    Args:
        model (Any): The model.

    Returns:
        Optional[str | int | UUID]: The id attribute.

    Raises:
        ValueError: if the model is not an object, BaseModel or dict or if no id attribute is available
    """
    # TODO: make this function faster!!
    if not is_identifiable(model):
        raise ValueError("Model is a basic type and has no id attribute.")

    if isinstance(model, BaseModel):
        identifiable_fields = get_identifier_type_fields(model.model_fields)
        if len(identifiable_fields) > 1:
            raise ValueError(f"Model has multiple Identifier attributes: {model}")
        if identifiable_fields:
            return getattr(model, identifiable_fields[0])
    elif hasattr(model, "__dict__"):
        # TODO: use typing.get_type_hints instead of inspect.signature
        sig = inspect.signature(type(model).__init__)
        potential_identifier = []
        for param in sig.parameters.values():
            if param.annotation == Identifier or param.annotation == "Identifier":
                potential_identifier.append(param.name)
        if len(potential_identifier) > 1:
            raise ValueError(f"Model {model} has multiple Identifier attributes.")
        if potential_identifier:
            return getattr(model, potential_identifier[0])
    if isinstance(model, BaseModel):
        data = model.model_dump()
    elif isinstance(model, dict):
        data = model
    else:
        data = vars(model)
    potential_id_attributes = [
        "id",
        "id_short",
        "Id",
        "ID",
        "Identifier",
        "identifier",
        "Identity",
        "identity",
    ]
    for id_attribute in potential_id_attributes:
        if id_attribute in data and isinstance(data[id_attribute], str | int | UUID):
            return data[id_attribute]

    raise ValueError(
        f"Model {model} has no attribute that can be used as id attribute."
    )


def get_id_with_patch(model: Any) -> str:
    """
    Function to get the id attribute of an arbitrary model.

    Args:
        model (Any): The model.

    Returns:
        Optional[str | int | UUID]: The id attribute.
    """
    if not is_identifiable(model):
        raise ValueError("Not identifiable object supplied.")
    try:
        return str(get_id(model))
    except ValueError:
        return "id_" + str(id(model))


def is_identifiable_type(schema: Type[Any]) -> bool:
    """
    Function to check if a schema is identifiable.

    Args:
        schema (Type[Any]): The schema.

    Returns:
        bool: True if the schema is identifiable, False otherwise.
    """
    # TODO: refactor to combine is_identifiable and is_identifiable_type
    # TODO: handle here also union types
    if not isinstance(schema, type) or typing.get_origin(schema) in [list, tuple, set]:
        return False
    if issubclass(schema, UnIdentifiable):
        return False
    return True


def get_identifiable_types(attribute_type: Type[Identifiable]) -> List[Type[Identifiable]]:
    identifiable_types = []
    if typing.get_origin(attribute_type) in [list, set, tuple, dict, Union]:
        attribute_types = typing.get_args(attribute_type)
        filtered_attribute_types = [arg for arg in attribute_types if arg != NoneType]
    else:
        return [attribute_type]
    for arg in filtered_attribute_types:
        identifiable_types += get_identifiable_types(arg)
    return identifiable_types

def is_identifiable_type_container(schema: Type[Any]) -> bool:
    """
    Method to check if a schema is a container of identifiables.

    Args:
        schema (Type[Any]): The schema.

    Returns:
        bool: True if the schema is a container of identifiables, False otherwise.
    """
    # TODO: refactor to combine is_identifiable_container and is_identifiable_type_container
    if typing.get_origin(schema):
        outer_type = typing.get_origin(schema)
    else:
        outer_type = schema

    if not outer_type in [list,  tuple, set, dict, Union]:
        return False
    if outer_type == dict:
        raise NotImplementedError("Dicts are not supported yet. Try using classes instead.")
    type_arguments = get_identifiable_types(schema)
    if not type_arguments:
        return False
    type_arguments_with_none = [arg for arg in type_arguments if arg != NoneType]
    if not all(is_identifiable_type(element) for element in type_arguments_with_none):
        return False
    return True


def is_identifiable_container(model: Any) -> bool:
    """
    Function to check if a model is an identifiable container.

    Args:
        model (Any): The model.

    Returns:
        bool: True if the model is an identifiable container, False otherwise.
    """
    if not model:
        return False
    if not isinstance(model, list | tuple | set | dict):
        return False

    if isinstance(model, dict):
    #     # return any(is_identifiable(k) or is_identifiable(v) for k, v in model.items())
    #     raise NotImplementedError("Dicts are not supported yet. Try using classes instead.")
        return True
    return any(is_identifiable(element) for element in model)


def get_values_as_identifiable_list(value: Any) -> List[Optional[Identifiable]]:
    if is_identifiable(value):
        return [value]
    elif is_identifiable_container(value):
        return value
    else:
        return []


def get_identifiable_attributes_dict_of_model(
    potential_identifiable_container: Identifiable,
) -> Dict[str, Identifiable]:
    referable_values = {}
    if not is_identifiable(potential_identifiable_container):
        return {}
    else:
        attribute_dict = vars(potential_identifiable_container)
    for attribute_name, attribute_value in attribute_dict.items():
        if not is_identifiable(attribute_value) or is_identifiable_container(attribute_value):
            continue
        referable_values[attribute_name] = attribute_value
    return referable_values


def get_identifiable_attributes_of_model(
    potential_identifiable_container: Identifiable,
) -> List[Identifiable]:
    referable_values = []
    if not is_identifiable(potential_identifiable_container):
        return []
    attribute_dict = vars(potential_identifiable_container)
    for attribute_value in attribute_dict.values():
        referable_values += get_values_as_identifiable_list(attribute_value)
    return referable_values

def get_unidentifiable_attributes_of_model(
    potential_identifiable_container: Identifiable,
) -> Dict[str, UnIdentifiable]:
    unidentifiable_values = {}
    if not is_identifiable(potential_identifiable_container):
        return []
    else:
        attribute_dict = vars(potential_identifiable_container)
    for attribute_name, attribute_value in attribute_dict.items():
        if isinstance(attribute_value, UnIdentifiable):
            unidentifiable_values[attribute_name] = attribute_value
    return unidentifiable_values

def add_non_redundant_identifiable(
    model_id:str, model: Identifiable, identifiable_map: Dict[str, Identifiable]
) -> Dict[str, Identifiable]:
    """
    Method to add an Identifiable to a list of Identifiables if it is not already in the list.

    Args:
        model_id (str): The id of the Identifiable.
        model (Identifiable): The Identifiable to add.
        identifiables (Dict[str, Identifiable]): The key map of contained Identifiables.

    Returns:
        Dict[str, Identifiable]: The key map of Identifiables with the added model.
    """
    if not model_id in identifiable_map:
        identifiable_map[model_id] = model
    return identifiable_map


def get_all_contained_identifiables(model: Identifiable) -> Dict[str, Identifiable]:
    """
    Method to iterate over an Identifiable model and get all contained Identifiables.

    Args:
        model (Identifiable): The Identifiable model.

    Returns:
        Dict[str, Identifiable]: The list of identifiables with their id as key.
    """
    contained_identifiables = {}
    identifiable_attributes = get_identifiable_attributes_of_model(model)
    for identifiable_attribute in identifiable_attributes:
        in_attribute_contained_identifiables = get_all_contained_identifiables(
            identifiable_attribute
        )
        for model_id, identifiable in in_attribute_contained_identifiables.items():
            add_non_redundant_identifiable(model_id, identifiable, contained_identifiables)
    if is_identifiable_container(model):
        for item in model:
            in_attribute_contained_identifiables = get_all_contained_identifiables(item)
            for model_id, identifiable in in_attribute_contained_identifiables.items():
                add_non_redundant_identifiable(model_id, identifiable, contained_identifiables)
    elif is_identifiable(model):
        model_id = get_id_with_patch(model)
        add_non_redundant_identifiable(model_id, model, contained_identifiables)
    return contained_identifiables


def get_references_of_reference_type_for_basemodel(model: BaseModel) -> List[str]:
    """
    Function to get the references of a model that are of type Reference.

    Args:
        model (BaseModel): The model.

    Returns:
        List[str]: The reference fields.
    """
    references = []
    for field_name, field_info in model.model_fields.items():
        if field_info.annotation == Reference or field_info.annotation == "Reference":
            references.append(getattr(model, field_name))
        if field_info.annotation == List[Reference]:
            references += getattr(model, field_name)
    return [str(ref) for ref in references if ref]


def get_references_of_reference_type_for_object(model: object) -> List[str]:
    """
    Function to get the references of a model that are of type Reference.

    Args:
        model (BaseModel): The model.

    Returns:
        List[str]: The reference fields.
    """
    references = []
    sig = inspect.signature(type(model).__init__)
    for param in sig.parameters.values():
        if param.annotation == Reference:
            references.append(getattr(model, param.name))
        if param.annotation == List[Reference]:
            references += getattr(model, param.name)
    return [str(ref) for ref in references if ref]


def get_referenced_ids_of_model(model: Identifiable) -> Set[str]:
    """
    Function to get the referenced ids of a model by searching for type Reference and attribute names which suggest references.

    Args:
        model (Referable): The model to get the references from.

    Returns:
        List[str]: The referenced ids.
    """
    referenced_ids = []
    if isinstance(model, BaseModel):
        referenced_ids += get_references_of_reference_type_for_basemodel(model)
    elif hasattr(model, "__dict__"):
        referenced_ids += get_references_of_reference_type_for_object(model)
    referenced_ids += get_attribute_name_encoded_references(model)
    return set(referenced_ids)


REFERENCE_ATTRIBUTE_NAMES_SUFFIXES = [
    "id",
    "ids",
    "Id",
    "Ids",
    "ID",
    "IDs",
    "Identifier",
    "Identifiers",
    "identity",
    "identities",
]

def get_reference_name(attribute_name: str, attribute_type: Type[Any]) -> Optional[str]:
    """
    Function to get the reference name of an attribute.

    Args:
        attribute_name (str): The attribute name.
        attribute_type (Type[Any]): The type of the attribute.

    Returns:
        str: The name of the referenced type.
    """
    if attribute_name in REFERENCE_ATTRIBUTE_NAMES_SUFFIXES or attribute_name in STANDARD_AAS_FIELDS:
        return 

    if attribute_type == Reference or attribute_type == "Reference":
        return attribute_name
    elif typing.get_origin(attribute_type) in [List, Set, Tuple, Union] and Reference in typing.get_args(attribute_type):
        return attribute_name
    elif any (attribute_name.endswith(suffix) for suffix in REFERENCE_ATTRIBUTE_NAMES_SUFFIXES):
        suffix = next(suffix for suffix in REFERENCE_ATTRIBUTE_NAMES_SUFFIXES if attribute_name.endswith(suffix))
        underscore_consideration = False
        if attribute_name.endswith(f"_{suffix}"):
            underscore_consideration = True
        attribute_name_without_suffix = attribute_name[:-(len(suffix) + underscore_consideration)]
        if attribute_name_without_suffix.endswith("s") and not attribute_name_without_suffix.endswith("ss"):
            attribute_name_without_suffix = attribute_name_without_suffix[:-1]
        return convert_under_score_to_camel_case_str(attribute_name_without_suffix)

def get_attribute_name_encoded_references(model: Identifiable) -> List[str]:
    """
    Function to get the referenced ids of a model.

    Args:
        model (Referable): The model.

    Returns:
        List[str]: The referenced ids.
    """
    referenced_ids = []
    for attribute_name, attribute_value in vars(model).items():
        if (
            attribute_name in STANDARD_AAS_FIELDS
            or attribute_name in REFERENCE_ATTRIBUTE_NAMES_SUFFIXES
        ):
            continue
        if not any(
            attribute_name.endswith(suffix)
            for suffix in REFERENCE_ATTRIBUTE_NAMES_SUFFIXES
        ):
            continue
        if not attribute_value:
            continue
        if isinstance(attribute_value, str | int | UUID):
            referenced_ids.append(str(attribute_value))
        elif isinstance(attribute_value, list | tuple | set):
            referenced_ids += [str(item) for item in attribute_value if item]
        else:
            raise ValueError(
                f"Attribute {attribute_name} of model {model} is not a reference."
            )
    return referenced_ids


def convert_to_fitting_identifiable_container_type(list_container: List[Identifiable], container_type: Type[Any]) -> List[Identifiable] | Tuple[Identifiable] | Set[Identifiable]:
    """
    Function to convert a list of identifiables to a fitting container type.

    Args:
        list_container (List[Identifiable]): The list of identifiables.
        container_type (Type[Any]): The container type.

    Returns:
        List[Identifiable] | Tuple[Identifiable] | Set[Identifiable]: The container type.
    """
    if container_type == list:
        return list_container
    elif container_type == tuple:
        return tuple(list_container)
    elif container_type == set:
        return set(list_container)
    else:
        raise ValueError("Container type not supported.")


def replace_attribute_with_model(model: Identifiable, existing_model: Identifiable):
    """
    Function to replace an attribute with a model.

    Args:
        model (Identifiable): The model.
        existing_model (Identifiable): The existing model.
    """
    for attribute_name, attribute_value in vars(model).items():
        if is_identifiable(attribute_value):
            if attribute_value == existing_model:
                setattr(model, attribute_name, existing_model)
            else:
                replace_attribute_with_model(attribute_value, existing_model)
        elif is_identifiable_container(attribute_value):
            list_attribute_value = list(attribute_value)
            for i, item in enumerate(list_attribute_value):
                if item == existing_model:
                    list_attribute_value[i] = existing_model
                else:
                    replace_attribute_with_model(item, existing_model)
            setattr(model, attribute_name, convert_to_fitting_identifiable_container_type(list_attribute_value, type(attribute_value)))


STANDARD_AAS_FIELDS = {"id", "description", "id_short", "semantic_id"}


def get_value_attributes(obj: object) -> Dict[str, Any]:
    """
    Function to get an dict of all attributes of an object without the private attributes and standard AAS attributes.

    Args:
        obj (object): The object.

    Returns:
        dict: The value attributes.
    """
    vars_dict = {}
    object_id = get_id_with_patch(obj)

    for attribute_name, attribute_value in vars(obj).items():
        if attribute_name.startswith("_"):
            continue
        if attribute_name in STANDARD_AAS_FIELDS:
            continue
        if attribute_value == object_id:
            continue
        if attribute_value is None:
            continue
        vars_dict[attribute_name] = attribute_value
    return vars_dict


def models_are_equal(model1: Identifiable, model2: Identifiable) -> bool:
    """
    Function to compare two models for equality.

    Args:
        model1 (Identifiable): The first model.
        model2 (Identifiable): The second model.

    Returns:
        bool: True if the models are equal, False otherwise.
    """
    model1_attributes = get_value_attributes(model1)
    model2_attributes = get_value_attributes(model2)
    if set(model1_attributes.keys()) != set(model2_attributes.keys()):
        return False
    for attribute_name1, attribute_value1 in model1_attributes.items():
        if is_identifiable(attribute_value1):
            if not models_are_equal(
                attribute_value1, model2_attributes[attribute_name1]
            ):
                return False
        elif is_identifiable_container(attribute_value1):
            if not is_identifiable_container(model2_attributes[attribute_name1]):
                return False
            if not len(attribute_value1) == len(model2_attributes[attribute_name1]):
                return False
            if not all(
                models_are_equal(item1, item2)
                for item1, item2 in zip(
                    attribute_value1, model2_attributes[attribute_name1]
                )
            ):
                return False
        elif attribute_value1 != model2_attributes[attribute_name1]:
            return False
    return True


def check_and_replace(model: Identifiable, id_map: Dict[str, Identifiable]) -> Identifiable:
        model_id = get_id_with_patch(model)

        # If the model is already in the id_map and the values are the same, return the cached model
        if model_id in id_map:
            existing_model = id_map[model_id]
            if not model.model_dump() == existing_model.model_dump():
                raise ValueError(
                    f"Duplicate models with id {model_id} have different values"
                )
            return existing_model
        # If it's not a duplicate, add it to the map and check nested models
        id_map[model_id] = model

        for field_name, field_value in get_identifiable_attributes_dict_of_model(model).items():
            if is_identifiable(field_value):
                setattr(model, field_name, check_and_replace(field_value, id_map))
            elif is_identifiable_container(field_value):
                normalized_list = [check_and_replace(item, id_map) for item in field_value]
                setattr(model, field_name, normalized_list)
        return model


def normalize_identifiables_in_model(models: List[Identifiable], id_map: Optional[Dict[str, Identifiable]] = None):
    """
    Normalize a list of Pydantic models by replacing duplicate models that share the same ID
    and have the same values.

    Args:
        model (Identifiable): List of Pydantic models (can be nested).
        id_map (Optional[Dict[str, Identifiable]]): A dictionary to store the mapping of IDs to models.
    """
    if id_map is None:
        id_map = {}
    local_id_map = dict(id_map)
    check_and_replace(models, local_id_map)


def normalize_identifiables(models: List[Identifiable]) -> List[Identifiable]:
    """
    Normalize a list of Pydantic models by replacing duplicate models that share the same ID
    and have the same values.

    Args:
        models (List[Identifiable]): List of Pydantic models (can be nested).

    Returns:
        List[Identifiable]: The normalized list of models.
    """
    id_map = {}
    new_models = []
    for model in models:
        new_models.append(check_and_replace(model, id_map))
    return new_models
