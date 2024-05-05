from __future__ import annotations
from enum import Enum
import re
from typing import Any, List, Union, TYPE_CHECKING, Optional, TypeVar

from aas_middleware.model.core import Referable
from pydantic import BaseModel, create_model


if TYPE_CHECKING:
    from aas_middleware.model.data_model import DataModel


BASIC_TYPE = Union[str, int, float, bool, None]
T = TypeVar("T", bound=Referable)

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
    if all(len(el) == 1 for el in new_class_name.split('_')):
        new_class_name = new_class_name.replace('_', '')
    return new_class_name

def convert_under_score_to_camel_case_str(underscore_str: str) -> str:
    """
    Convert a underscore seperated string to a camel case string.

    Args:
        class_name (str): The underscore seperated string to convert.

    Returns:
        str: The camel case string.
    """
    words = underscore_str.split('_')
    camel_case_str = ''.join(word.title() for word in words)
    return camel_case_str




def assure_id_short_attribute(model: Any) -> Any:
    if (
        not hasattr(model, "__dict__")
        or hasattr(model, "id_short")
        or isinstance(model, Enum)
        or not model
    ):
        return model
    id_attributes = ["id", "Id", "ID", "Identifier", "identifier", "Identity", "identity"]
    for attr in id_attributes:
        if hasattr(model, attr) and isinstance(getattr(model, attr), str):
            id_short = getattr(model, attr)
            break
    else:
        # TODO: add also Reference to specify the type of the id_short
        if isinstance(model, BaseModel):
            id_short = str(id(model))
        else:
            return model
            # raise ValueError(
            #     f"Model {model} has no id_short attribute and no id, Id or ID attribute. It is not a BaseModel and therefore cannot be used as a referable."
            # )
    
    if not isinstance(model, BaseModel):
        model.id_short = id_short
        return model

    class_name = model.__class__.__name__.split(".")[-1]
    new_model = create_model(class_name, __base__=model.__class__, id_short= (str, ...))
    
    model_dict = vars(model)
    model_dict["id_short"] = id_short
    return new_model(**model_dict)

def assure_id_short_attribute_of_list(model_list: List[Any]) -> List[Any]:
    return [assure_id_short_attribute(model) for model in model_list]

def is_referable(potential_referable: Any) -> bool:
    return hasattr(potential_referable, "id_short")


def is_instance_of_referables_list(potential_referables_list: Any) -> bool:
    return isinstance(potential_referables_list, (list, tuple, set)) and all(
        is_referable(item) for item in potential_referables_list
    )


def is_instance_of_basic_types_list(potential_basic_types_list: Any) -> bool:
    return isinstance(potential_basic_types_list, (list, tuple, set)) and all(
        isinstance(item, BASIC_TYPE) for item in potential_basic_types_list
    )


def get_underscore_class_name_from_model(model: Referable) -> str:
    class_name = model.__class__.__name__.split(".")[-1]
    attribute_name = convert_camel_case_to_underscrore_str(class_name)
    return attribute_name


def get_referable_list_of_value(value: Any) -> Optional[List[Referable]]:
    if isinstance(value, (list, tuple, set)):
        value = assure_id_short_attribute_of_list(value)
    else:
        value = assure_id_short_attribute(value)
    if is_referable(value):
        return [value]
    elif is_instance_of_referables_list(value):
        return value
    else:
        return []


def get_referable_attributes_of_model(
    potential_referable_container: Union[Referable, List[Referable]]
) -> List[Referable]:
    referable_values = []
    if not hasattr(potential_referable_container, "__dict__"):
        return []
    else:
        attribute_dict = vars(potential_referable_container)
    for attribute_value in attribute_dict.values():
        referable_values += get_referable_list_of_value(attribute_value)
    return referable_values


def add_non_redundant_referable(
    referable: Referable, referables: List[Referable]
) -> List[Referable]:
    """
    Method to add a referable to a list of referables if it is not already in the list.

    Args:
        referable (Referable): The referable to add.
        referables (List[Referable]): The list of referables.

    Returns:
        List[Referable]: The list of referables with the added referable.
    """
    if not any(
        referable.id_short == other_referable.id_short for other_referable in referables
    ):
        referables.append(referable)
    return referables


def get_all_contained_referables(
    model: Union[Referable, List[Referable]]
) -> List[Referable]:
    """
    Method to iterate over a referable data model and get all referables.

    Args:
        model (REFERABLE_DATA_MODEL): The referable data model.

    Returns:
        List[Referable]: The list of referables.
    """
    referables = []
    referable_attributes = get_referable_attributes_of_model(model)
    for referable_attribute in referable_attributes:
        new_referables = get_all_contained_referables(referable_attribute)
        for referable in new_referables:
            add_non_redundant_referable(referable, referables)
    if is_instance_of_referables_list(model):
        model = assure_id_short_attribute_of_list(model)
        for item in model:
            new_referables = get_all_contained_referables(item)
            for referable in new_referables:
                add_non_redundant_referable(referable, referables)
    elif is_referable(model):
        model = assure_id_short_attribute(model)
        add_non_redundant_referable(model, referables)
    return referables


def get_referenced_ids_of_model(model: Referable) -> List[str]:
    """
    Function to get the referenced ids of a model.

    Args:
        model (Referable): The model.

    Returns:
        List[str]: The referenced ids.
    """
    referenced_ids = []
    for attribute_name, attribute_value in vars(model).items():
        if attribute_name.split("_")[-1] == "id" and attribute_name != "semantic_id":
            if attribute_value:
                referenced_ids.append(attribute_value)
        elif attribute_name.split("_")[-1] == "ids":
            if attribute_value:
                referenced_ids += attribute_value
    return referenced_ids


def replace_attribute_with_model(model: Referable, existing_model: Referable):
    """
    Function to replace an attribute with a model.

    Args:
        model (Referable): The model.
        existing_model (Referable): The existing model.
    """
    for attribute_name, attribute_value in vars(model).items():
        if is_referable(attribute_value):
            if attribute_value == existing_model:
                setattr(model, attribute_name, existing_model)
            else:
                replace_attribute_with_model(attribute_value, existing_model)
        elif is_instance_of_referables_list(attribute_value):
            for i, item in enumerate(attribute_value):
                if item == existing_model:
                    attribute_value[i] = existing_model
                else:
                    replace_attribute_with_model(item, existing_model)
