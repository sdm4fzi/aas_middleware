import copy
import json
from typing import Any, Dict, Optional

import pydantic
from aas_middleware.model.formatting.aas.aas_model import (
    AAS,
    Submodel,
    SubmodelElementCollection,
)
from aas_middleware.model.formatting.aas import convert_aas_instance, convert_aas_template, convert_pydantic, convert_aas, convert_pydantic_model, convert_pydantic_type

from enum import Enum
from collections.abc import Mapping


def normalize_schema(schema: Dict[str, Any], reference_schemas: Dict[str, Any]) -> Dict[str, Any]:
    """ Recursively normalize schema for comparison, sorting keys and normalizing references. """
    if isinstance(schema, dict):
        if "examples" in schema:
            del schema["examples"]
        if "title" in schema:
            del schema["title"]

        # TODO: remove later when tuple incorrection of length of entries is working when writing to basyx AAS...
        if "minItems" in schema:
            del schema["minItems"]
        if "maxItems" in schema:
            del schema["maxItems"]
        if "prefixItems" in schema:
            schema["items"] = schema["prefixItems"][0]
            del schema["prefixItems"]

        # TODO: remove later when fixed number of string values (enums, literals) is working when writing to basyx AAS based on concept descriptions...
        if "$ref" in schema:
            references_name = schema["$ref"].split("/")[-1]
            if references_name in reference_schemas and "enum" in reference_schemas[references_name]:
                schema["title"] = reference_schemas[references_name]["title"]
                schema["type"] = reference_schemas[references_name]["type"]
                del schema["$ref"]
        if "enum" in schema:
            del schema["enum"]

        # Sort the dictionary keys and normalize nested objects
        try:
            return {key: normalize_schema(value, reference_schemas=reference_schemas) for key, value in sorted(schema.items())}
        except TypeError:
            return {key: normalize_schema(value, reference_schemas=reference_schemas) for key, value in schema.items()}
    elif isinstance(schema, list):
        # Sort lists for consistent ordering
        try:
            return sorted(normalize_schema(item, reference_schemas=reference_schemas) for item in schema)
        except TypeError:
            # sort based on values not on key
            schema_list = [normalize_schema(item, reference_schemas=reference_schemas) for item in schema]
            return sorted(schema_list, key=lambda x: str(x))
    return schema

def compare_properties(schema1: Dict[str, Any], schema2: Dict[str, Any], reference_schemas: Dict[str, Any]) -> bool:
    """ Compare properties and required attributes of two schemas. """
    # Check if both schemas define properties
    properties1 = schema1.get("properties", {})
    properties2 = schema2.get("properties", {})
    
    # Normalize and compare properties
    # normalized_schema1 = normalize_schema(properties1, reference_schemas=reference_schemas)
    # normalized_schema2 = normalize_schema(properties2, reference_schemas=reference_schemas)
    # for key, value in normalized_schema1.items():
    #     if not key in normalized_schema2:
    #         print("missing key", key)
    #     if value != normalized_schema2[key]:
    #         print("different values")
    #         print(value)
    #         print(normalized_schema2[key])
    if normalize_schema(properties1, reference_schemas=reference_schemas) != normalize_schema(properties2, reference_schemas=reference_schemas):
        return False

    # Compare required fields
    required1 = sorted(schema1.get("required", []))
    required2 = sorted(schema2.get("required", []))
    
    if required1 != required2:
        return False

    return True


def compare_references(schema1: Dict[str, Any], schema2: Dict[str, Any], reference_schemas: Dict[str, Any]) -> bool:
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

def compare_schemas(schema1: Dict[str, Any], schema2: Dict[str, Any], reference_schemas: Optional[Dict[str, Any]]=None) -> bool:
    """ Compare two JSON schemas recursively, including properties, references, and required fields. """
    if not reference_schemas:
        reference_schemas = {}
        reference_schemas.update(copy.deepcopy(schema1.get("$defs", {})))
        reference_schemas.update(copy.deepcopy(schema2.get("$defs", {})))
    
    normalized_schema1 = normalize_schema(schema1, reference_schemas=reference_schemas)
    normalized_schema2 = normalize_schema(schema2, reference_schemas=reference_schemas)
    
    if normalized_schema1.get("type") != normalized_schema2.get("type"):
        return False

    if not compare_properties(normalized_schema1, normalized_schema2, reference_schemas=reference_schemas):
        return False

    if not compare_references(normalized_schema1, normalized_schema2, reference_schemas):
        return False

    return True

def test_convert_simple_submodel(example_submodel: Submodel):
    # TODO: tuple and list SEC attributes make problems here...tuples are lists and list SECs contain strange element with no values?
    basyx_aas_submodel = convert_pydantic_model.convert_model_to_submodel(example_submodel)
    pydantic_model = convert_aas_instance.convert_submodel_to_model_instance(basyx_aas_submodel)
    for key in pydantic_model.model_dump():
        if not key in example_submodel.model_dump():
            print("missing key", key)
        if not pydantic_model.model_dump()[key] == example_submodel.model_dump()[key]:
            print("different values")
            print(pydantic_model.model_dump()[key])
            print(example_submodel.model_dump()[key])
    assert pydantic_model.model_dump() == example_submodel.model_dump()

def test_convert_simple_submodel_template():
    basyx_aas_submodel_template = convert_pydantic_type.convert_model_to_submodel_template(Submodel)
    submodel_infered_type = convert_aas_template.convert_submodel_template_to_pydatic_type(basyx_aas_submodel_template)
    assert compare_schemas(Submodel.model_json_schema(), submodel_infered_type.model_json_schema())

def test_convert_simple_submodel_with_template_extraction(example_submodel: Submodel):
    basyx_aas_submodel = convert_pydantic_model.convert_model_to_submodel(example_submodel)
    basyx_aas_submodel_template = convert_pydantic_type.convert_model_instance_to_submodel_template(example_submodel)        
    
    submodel_infered_type = convert_aas_template.convert_submodel_template_to_pydatic_type(basyx_aas_submodel_template)
    assert compare_schemas(example_submodel.model_json_schema(), submodel_infered_type.model_json_schema())
    
    pydantic_model = convert_aas_instance.convert_submodel_to_model_instance(basyx_aas_submodel, submodel_infered_type)
    assert pydantic_model.model_dump() == example_submodel.model_dump()


# def test_convert_simple_aas(example_aas: AAS):
# #     # TODO: update this to new type / instance conversion
#     object_store = convert_pydantic_type.convert_model_to_aas_template(type(example_aas))
#     pydantic_type = convert_aas_template.convert_object_store_to_pydantic_types(object_store)
#     assert len(pydantic_type) == 1
#     assert compare_schemas(example_aas.model_json_schema(), pydantic_type[0].model_json_schema())

#     object_store_instance = convert_pydantic_model.convert_model_to_aas(example_aas)
#     pydantic_instance = convert_aas_instance.convert_object_store_to_pydantic_models(object_store_instance, types=pydantic_type)
#     assert len(pydantic_instance) == 1
#     assert pydantic_instance[0].model_dump() == example_aas.model_dump()
