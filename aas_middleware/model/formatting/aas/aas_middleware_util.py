import json
import re
from typing import List, Tuple, Type, Dict
from basyx.aas import model

from pydantic import BaseModel, ConfigDict, create_model
import typing

from pydantic.fields import FieldInfo
from aas_middleware.model.formatting.aas import aas_model


def convert_under_score_to_camel_case_str(underscore_str: str) -> str:
    """
    Convert a underscore seperated string to a camel case string.

    Args:
        class_name (str): The underscore seperated string to convert.

    Returns:
        str: The camel case string.
    """
    words = underscore_str.split("_")
    camel_case_str = "".join(word.title() for word in words)
    return camel_case_str


def save_model_list_with_schema(model_list: typing.List[BaseModel], path: str):
    """
    Saves a list of pydantic models to a json file.
    Args:
        model_list (typing.List[aas_model.AAS]): List of pydantic models
        path (str): Path to the json file
    """
    save_dict = {
        "models": [model.model_dump() for model in model_list],
        "schema": [model.model_json_schema() for model in model_list],
    }

    with open(path, "w", encoding="utf-8") as json_file:
        json.dump(save_dict, json_file, indent=4)


def get_contained_models_attribute_info(
    model: Type[BaseModel],
) -> List[Tuple[str, Type[aas_model.Submodel]]]:
    """
    Function to get all submodels from a pydantic model
    Args:
        model (Type[BaseModel]): The pydantic model to get the submodels from
    Returns:
        List[Tuple[str, Type[aas_model.Submodel]]]: List of attribute name and value of all submodels in the pydantic model
    """
    submodels = []
    for attribute_name, fieldinfo in model.model_fields.items():
        if typing.get_args(fieldinfo.annotation) != () and any(issubclass(arg, aas_model.Submodel) for arg in typing.get_args(fieldinfo.annotation)):
            submodels.append((attribute_name, fieldinfo.annotation))
        elif issubclass(fieldinfo.annotation, aas_model.Submodel):
            submodels.append((attribute_name, fieldinfo.annotation))
    return submodels


def get_all_submodel_elements_from_submodel(
    model: Type[aas_model.Submodel],
) -> Dict[
    str, Type[aas_model.SubmodelElementCollection | list | str | bool | float | int]
]:
    """
    Function to get all submodel elements from a pydantic submodel

    Args:
        model (Type[BaseModel]): The pydantic submodel to get the submodel elements from

    Returns:
        List[aas_model.SubmodelElementCollection | list | str | bool | float | int]: A list of all submodel elements in the pydantic submodel
    """
    submodel_elements = {}
    for field_name, field_info in model.model_fields.items():
        if (
            field_name != "description"
            and field_name != "id_short"
            and field_name != "semantic_id"
            and field_name != "id"
        ):
            submodel_elements[field_name] = field_info.annotation
    return submodel_elements


def get_all_submodels_from_object_store(
    obj_store: model.DictObjectStore,
) -> List[model.Submodel]:
    """
    Function to get all basyx submodels from an object store
    Args:
        obj_store (model.DictObjectStore): Object store to get submodels from
    Returns:
        List[model.Submodel]: List of basyx submodels
    """
    submodels = []
    for item in obj_store:
        if isinstance(item, model.Submodel):
            submodels.append(item)
    return submodels


def get_field_default_value(fieldinfo: FieldInfo) -> typing.Any:
    """
    Function to get the default values of a pydantic model field. If no default is given, the function tries to infer a default cored on the type.

    Args:
        fieldinfo (FieldInfo): Pydantic model field.

    Returns:
        typing.Any: Missing default value.
    """
    if fieldinfo.default:
        return fieldinfo.default
    elif fieldinfo.default_factory:
        return fieldinfo.default_factory()
    elif fieldinfo.annotation == str:
        return "string"
    elif fieldinfo.annotation == bool:
        return False
    elif fieldinfo.annotation == int:
        return 1
    elif fieldinfo.annotation == float:
        return 1.0
    elif fieldinfo.annotation == list:
        return []


def set_example_values(model: Type[BaseModel]) -> Type[BaseModel]:
    """
    Sets the example values of a pydantic model cored on its default values.

    Args:
        model (Type[BaseModel]): Pydantic model.

    Returns:
        Type[BaseModel]: Pydantic model with the example values set.
    """
    # TODO: potentially delete this method, since not required...
    example_dict = {}
    for field_name, fieldinfo in model.model_fields.items():
        if issubclass(fieldinfo.annotation, BaseModel):
            config_dict = ConfigDict(
                json_schema_extra={"examples": [fieldinfo.default.model_dump_json()]}
            )
            fieldinfo.annotation.model_config = config_dict
        example_dict[field_name] = get_field_default_value(fieldinfo)
    serialized_example = model(**example_dict).model_dump_json()
    config_dict = ConfigDict(json_schema_extra={"examples": [serialized_example]})
    model.model_config = config_dict
    return model


def core_model_check(fieldinfo: FieldInfo) -> bool:
    """
    Checks if a pydantic model field is a core model.

    Args:
        fieldinfo (FieldInfo): Pydantic model field.

    Returns:
        bool: If the model field is a core model.
    """
    if isinstance(fieldinfo.default, BaseModel):
        return True
    if typing.get_origin(fieldinfo.annotation) is typing.Union:
        args = typing.get_args(fieldinfo.annotation)
        if all(issubclass(arg, BaseModel) for arg in args):
            return True
    else:
        if issubclass(fieldinfo.annotation, BaseModel):
            return True


def is_basemodel_union_type(model: Type) -> bool:
    """
    Checks if a type is a union type.

    Args:
        model (Type): Type.

    Returns:
        bool: If the type is a union type.
    """
    if typing.get_origin(model) == typing.Union:
        args = typing.get_args(model)
        if all(issubclass(arg, BaseModel) for arg in args):
            return True
        else:
            False
    else:
        return False
    

def is_optional_type(model: Type) -> bool:
    """
    Checks if a type is an optional type.

    Args:
        model (Type): Type.

    Returns:
        bool: If the type is an optional type.
    """
    if typing.get_origin(model) == typing.Union:
        args = typing.get_args(model)
        if any(arg == type(None) for arg in args):
            return True
        else:
            return False
    else:
        return False


def union_type_field_check(fieldinfo: FieldInfo) -> bool:
    """
    Checks if a pydantic model field is a union type.

    Args:
        fieldinfo (FieldInfo): Pydantic model field.

    Returns:
        bool: If the model field is a union type.
    """
    return is_basemodel_union_type(fieldinfo.annotation)


def set_required_fields(
    model: Type[BaseModel], origin_model: Type[BaseModel]
) -> Type[BaseModel]:
    """
    Sets the required fields of a pydantic model.

    Args:
        model (Type[BaseModel]): Pydantic model.
        origin_model (Type[BaseModel]): Pydantic model from which the required fields should be copied.

    Returns:
        Type[BaseModel]: Pydantic model with the required fields set.
    """
    # TODO: potentially delete this method, since not required in pydantic v2
    for field_name, fieldinfo in origin_model.model_fields.items():
        if union_type_field_check(fieldinfo):
            original_sub_types = typing.get_args(fieldinfo.annotation)
            model_sub_types = typing.get_args(model.model_fields[field_name].annotation)
            new_types = []
            for original_sub_type, model_sub_type in zip(
                original_sub_types, model_sub_types
            ):
                new_type = set_required_fields(model_sub_type, original_sub_type)
                new_types.append(new_type)
            model.model_fields[field_name].annotation = typing.Union[tuple(new_types)]
        elif core_model_check(fieldinfo):
            new_type = set_required_fields(
                model.model_fields[field_name].annotation, fieldinfo.annotation
            )
            model.model_fields[field_name].annotation = new_type
        if fieldinfo.is_required():
            model.model_fields[field_name].default = None
            model.model_fields[field_name].default_factory = True
    return model


def set_default_values(
    model: Type[BaseModel], origin_model: Type[BaseModel]
) -> Type[BaseModel]:
    """
    Sets the default values and default factory of a pydantic model cored on a original model.

    Args:
        model (Type[BaseModel]): Pydantic model where default values should be removed.

    Returns:
        Type[BaseModel]: Pydantic model with the default values set.
    """
    # TODO: validate if this method is still needed in pydantic 2.0
    for field_name, fieldinfo in origin_model.model_fields.items():
        if union_type_field_check(fieldinfo):
            original_sub_types = typing.get_args(fieldinfo.annotation)
            model_sub_types = typing.get_args(model.model_fields[field_name].annotation)
            new_types = []
            for original_sub_type, model_sub_type in zip(
                original_sub_types, model_sub_types
            ):
                new_type = set_default_values(model_sub_type, original_sub_type)
                new_types.append(new_type)
            model.model_fields[field_name].annotation = typing.Union[tuple(new_types)]
        elif core_model_check(fieldinfo):
            new_type = set_default_values(
                model.model_fields[field_name].annotation, fieldinfo.annotation
            )
            model.model_fields[field_name].annotation = new_type
        if not fieldinfo.is_required() and (
            fieldinfo.default
            or fieldinfo.default == ""
            or fieldinfo.default == 0
            or fieldinfo.default == 0.0
            or fieldinfo.default == False
            or fieldinfo.default == []
            or fieldinfo.default == {}
        ):
            model.model_fields[field_name].default = fieldinfo.default
        else:
            model.model_fields[field_name].default = None

        if not fieldinfo.is_required() and fieldinfo.default_factory:
            model.model_fields[field_name].default_factory = fieldinfo.default_factory
        else:
            model.model_fields[field_name].default_factory = None
    return model


def get_pydantic_models_from_instances(
    instances: List[BaseModel],
) -> List[Type[BaseModel]]:
    """
    Functions that creates pydantic models from instances.

    Args:
        instances (typing.List[BaseModel]): List of pydantic model instances.

    Returns:
        List[Type[BaseModel]]: List of pydantic models.
    """
    # TODO: update method with pydantic v2 arguments of create_model
    models = []
    for instance in instances:
        model_name = type(instance).__name__
        pydantic_model = create_model(model_name, **vars(instance))
        pydantic_model = set_example_values(pydantic_model)
        pydantic_model = set_required_fields(pydantic_model, instance.__class__)
        pydantic_model = set_default_values(pydantic_model, instance.__class__)
        models.append(pydantic_model)
    return models


def recusrive_model_creation(model_name, dict_values, depth=0):
    """
    Function that creates a pydantic model from a dict.

    Args:
        model_name (_type_): _description_
        dict_values (_type_): _description_

    Returns:
        _type_: _description_
    """
    # TODO: check function below if needed
    for attribute_name, attribute_values in dict_values.items():
        if isinstance(attribute_values, dict):
            class_name = convert_under_score_to_camel_case_str(attribute_name)
            created_model = recusrive_model_creation(
                class_name, attribute_values, depth=depth + 1
            )
            dict_values[attribute_name] = created_model(**attribute_values)
    if depth == 0:
        core_class = aas_model.AAS
    elif depth == 1:
        core_class = aas_model.Submodel
    else:
        core_class = aas_model.SubmodelElementCollection
    return create_model(model_name, **dict_values, __core__=core_class)


def get_pydantic_model_from_dict(
    dict_values: dict, model_name: str, all_fields_required: bool = False
) -> Type[BaseModel]:
    """
    Functions that creates pydantic model from dict.

    Args:
        dict_values (dict): Dictionary of values.
        model_name (str): Name of the model.
        all_fields_required (bool, optional): If all fields should be required (non-Optional) in the model. Defaults to False.
    Returns:
        Type[BaseModel]: Pydantic model.
    """
    # TODO: check function below if needed...
    pydantic_model = recusrive_model_creation(model_name, dict_values)
    pydantic_model = set_example_values(pydantic_model)
    if all_fields_required:
        for field_name, field_info in pydantic_model.model_fields.items():
            field_info.default = None
    return pydantic_model


def remove_empty_lists(dictionary: dict) -> None:
    keys_to_remove = []
    for key, value in dictionary.items():
        if isinstance(value, dict):
            # Recursively process nested dictionaries
            remove_empty_lists(value)
            # if not value:
            #     keys_to_remove.append(key)
        elif isinstance(value, list) and value:
            # Recursively process nested lists
            for item in value:
                if isinstance(item, dict):
                    remove_empty_lists(item)
        elif isinstance(value, list) and not value:
            keys_to_remove.append(key)
    for key in keys_to_remove:
        del dictionary[key]
