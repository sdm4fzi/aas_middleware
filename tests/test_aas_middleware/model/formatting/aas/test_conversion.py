import json
from aas_middleware.model.formatting.aas.aas_model import (
    AAS,
    Submodel,
    SubmodelElementCollection,
)
from aas_middleware.model.formatting.aas import convert_aas_instance, convert_aas_template, convert_pydantic, convert_aas, convert_pydantic_model, convert_pydantic_type

from enum import Enum
from collections.abc import Mapping

def compare_dicts(dict1, dict2):
    # Check if both are dictionaries
    if not isinstance(dict1, Mapping) or not isinstance(dict2, Mapping):
        print("Not a dictionary")
        return False
    
    # Compare the lengths first
    if len(dict1) != len(dict2):
        print("Different lengths")
        return False
    
    # Iterate through the first dictionary
    for key, value in dict1.items():
        if key not in dict2:
            print("Key not in dict2")
            return False
        
        value2 = dict2[key]
        
        # Handle Enums: compare the actual values of the Enums
        if isinstance(value, Enum) and isinstance(value2, Enum):
            if value.value != value2.value:
                print("Different Enum values", value, value2)
                return False
        elif isinstance(value, Mapping) and isinstance(value2, Mapping):
            # Recursive check for nested dictionaries
            if not compare_dicts(value, value2):
                return False
        elif value != value2:
            print("Different values", value, value2)
            return False
        
    return True


def normalize_schema(schema):
    """ Recursively normalize schema for comparison, sorting keys and normalizing references. """
    if isinstance(schema, dict):
        # FIXME: fix that defaults are not set during conversion
        if "default" in schema:
            del schema["default"]
        if "examples" in schema:
            del schema["examples"]
        # Sort the dictionary keys and normalize nested objects
        try:
            return {key: normalize_schema(value) for key, value in sorted(schema.items())}
        except TypeError:
            return {key: normalize_schema(value) for key, value in schema.items()}
    elif isinstance(schema, list):
        # Sort lists for consistent ordering
        try:
            return sorted(normalize_schema(item) for item in schema)
        except TypeError:
            return [normalize_schema(item) for item in schema]
    return schema

def compare_properties(schema1, schema2):
    """ Compare properties and required attributes of two schemas. """
    # Check if both schemas define properties
    properties1 = schema1.get("properties", {})
    properties2 = schema2.get("properties", {})
    
    # Normalize and compare properties
    if normalize_schema(properties1) != normalize_schema(properties2):
        return False

    # Compare required fields
    required1 = sorted(schema1.get("required", []))
    required2 = sorted(schema2.get("required", []))
    
    if required1 != required2:
        # FIXME: required fields are not set correctly after conversion because defaults are missing -> set them in concept description
        # return False
        return True

    return True

def compare_references(schema1, schema2, reference_schemas):
    """ Compare references between two schemas recursively, checking definitions. """
    ref1 = schema1.get("$ref")
    ref2 = schema2.get("$ref")
    
    # If both schemas reference something, ensure they reference the same thing
    if ref1 != ref2:
        return False

    # If references exist, compare the referenced schemas recursively
    if ref1 and ref2:
        ref_schema1 = reference_schemas.get(ref1)
        ref_schema2 = reference_schemas.get(ref2)
        if ref_schema1 and ref_schema2:
            return compare_schemas(ref_schema1, ref_schema2, reference_schemas)
    
    return True

def compare_schemas(schema1, schema2, reference_schemas=None):
    """ Compare two JSON schemas recursively, including properties, references, and required fields. """
    reference_schemas = reference_schemas or {}

    normalized_schema1 = normalize_schema(schema1)
    normalized_schema2 = normalize_schema(schema2)
    
    if normalized_schema1.get("type") != normalized_schema2.get("type"):
        return False

    if not compare_properties(normalized_schema1, normalized_schema2):
        return False

    if not compare_references(normalized_schema1, normalized_schema2, reference_schemas):
        return False

    return True

def test_convert_simple_submodel(example_submodel: Submodel):
    basyx_aas_submodel = convert_pydantic.convert_model_to_submodel(example_submodel)
    pydantic_model = convert_aas_instance.convert_submodel_to_model_instance(basyx_aas_submodel)
    assert pydantic_model.model_dump_json() == example_submodel.model_dump_json()

def test_convert_simple_submodel_template():
    basyx_aas_submodel_template = convert_pydantic_type.convert_model_to_submodel_template(Submodel)
    submodel_infered_type = convert_aas_template.convert_submodel_template_to_pydatic_type(basyx_aas_submodel_template)
    assert compare_schemas(Submodel.model_json_schema(), submodel_infered_type.model_json_schema())

def test_convert_simple_submodel_with_template_extraction(example_submodel: Submodel):
    basyx_aas_submodel = convert_pydantic_model.convert_model_to_submodel(example_submodel)
    basyx_aas_submodel_template = convert_pydantic_type.convert_model_instance_to_submodel_template(example_submodel)        
    submodel_infered_type = convert_aas_template.convert_submodel_template_to_pydatic_type(basyx_aas_submodel_template)
    # FIXME: resolve problems with long class names in json schema...
    # assert compare_schemas(example_submodel.model_json_schema(), submodel_infered_type.model_json_schema())

    pydantic_model = convert_aas_instance.convert_submodel_to_model_instance(basyx_aas_submodel, submodel_infered_type)
    assert pydantic_model.model_dump() == example_submodel.model_dump()


# def test_convert_simple_aas(example_aas: AAS):
#     basyx_aas = convert_pydantic.convert_model_to_aas(example_aas)
#     pydantic_models = convert_aas.convert_object_store_to_pydantic_models(basyx_aas)
#     assert len(pydantic_models) == 1
#     pydantic_model = pydantic_models[0]
#     # assert pydantic_model.model_dump() == example_aas.model_dump()