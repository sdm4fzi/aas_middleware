from __future__ import annotations

import inspect
from typing import Dict, List, Type
import typing

from pydantic import ConfigDict, BaseModel

from aas_middleware.model.core import Identifiable, Reference
from aas_middleware.model.util import is_identifiable_type, is_identifiable_type_container


def get_attribute_dict_of_schema(schema: Type[Identifiable]) -> Dict[str, Type[Identifiable]]:
    """
    Method to get all attributes of a model.

    Args:
        model (Type[Identifiable]): The referable data model.

    Returns:
        Dict[str, Type[Identifiable]]: The dictionary of attributes.
    """
    attribute_dict = {}
    if not isinstance(schema, type):
        return attribute_dict
    if not typing.get_origin(schema) and issubclass(schema, BaseModel):
        for field_name, field in schema.model_fields.items():
            attribute_dict[field_name] = field.annotation
    else:
        annotations = typing.get_type_hints(schema.__init__)
        for parameter_name, parameter in annotations.items():
            attribute_dict[parameter_name] = parameter
    return attribute_dict


def get_identifiable_attributes(schema: Type[Identifiable]) -> Dict[str, Type[Identifiable]]:
    """
    Method to get all attributes of a model.

    Args:
        schema (Type[Identifiable]): The referable data model.

    Returns:
        List[str]: The list of attributes.
    """
    schema_attributes = get_attribute_dict_of_schema(schema)
    identifiable_attributes = {}
    for attribute_name, attribute_type in schema_attributes.items():
        if is_identifiable_type(attribute_type) or is_identifiable_type_container(attribute_type):
            identifiable_attributes[attribute_name] = attribute_type

    return identifiable_attributes
            



def add_non_redundant_schema(schema: Type[Identifiable], schemas: List[Type[Identifiable]]):
    """
    Method to add a schema to a list of schemas if it is not already in the list.

    Args:
        schema (Type[Identifiable]): The schema to add.
        schemas (List[Type[Identifiable]]): The list of schemas.
    """
    if schema not in schemas:
        schemas.append(schema)

def get_all_contained_schemas(schema: Type[Identifiable]) -> List[Type[Identifiable]]:
    """
    Method to iterate over an Identifiable model and get all contained Identifiables.

    Args:
        schema (Type[Identifiable]): The referable data model.

    Returns:
        List[Type[Referable]]: The list of referables.
    """
    contained_schemas = []
    identifiable_schema_attributes = get_identifiable_attributes(schema)
    for identifiable_schema_attribute in identifiable_schema_attributes.values():
        in_attribute_contained_identifiable_schema = get_all_contained_schemas(
            identifiable_schema_attribute
        )
        for schema_attribute in in_attribute_contained_identifiable_schema:
            add_non_redundant_schema(schema_attribute, contained_schemas)
    if is_identifiable_type_container(schema):
        for item in typing.get_args(schema):
            in_attribute_contained_identifiable_schema = get_all_contained_schemas(item)
            for schema_attribute in in_attribute_contained_identifiable_schema:
                add_non_redundant_schema(schema_attribute, contained_schemas)
    elif is_identifiable_type(schema):
        add_non_redundant_schema(schema, contained_schemas)
    return contained_schemas
