from typing import Any, Dict, Optional
import copy


def normalize_schema(
    schema: Dict[str, Any], reference_schemas: Dict[str, Any]
) -> Dict[str, Any]:
    """Recursively normalize schema for comparison, sorting keys and normalizing references."""
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
            if (
                references_name in reference_schemas
                and "enum" in reference_schemas[references_name]
            ):
                schema["title"] = reference_schemas[references_name]["title"]
                schema["type"] = reference_schemas[references_name]["type"]
                del schema["$ref"]
        if "enum" in schema:
            del schema["enum"]

        # Sort the dictionary keys and normalize nested objects
        try:
            return {
                key: normalize_schema(value, reference_schemas=reference_schemas)
                for key, value in sorted(schema.items())
            }
        except TypeError:
            return {
                key: normalize_schema(value, reference_schemas=reference_schemas)
                for key, value in schema.items()
            }
    elif isinstance(schema, list):
        # Sort lists for consistent ordering
        try:
            return sorted(
                normalize_schema(item, reference_schemas=reference_schemas)
                for item in schema
            )
        except TypeError:
            # sort based on values not on key
            schema_list = [
                normalize_schema(item, reference_schemas=reference_schemas)
                for item in schema
            ]
            return sorted(schema_list, key=lambda x: str(x))
    return schema


def compare_properties(
    schema1: Dict[str, Any], schema2: Dict[str, Any], reference_schemas: Dict[str, Any], ignore_tuple_type_hints: bool = False
) -> bool:
    """Compare properties and required attributes of two schemas."""
    # Check if both schemas define properties
    properties1 = schema1.get("properties", {})
    properties2 = schema2.get("properties", {})

    # Normalize and compare properties
    normalized_schema1 = normalize_schema(
        properties1, reference_schemas=reference_schemas
    )
    normalized_schema2 = normalize_schema(
        properties2, reference_schemas=reference_schemas
    )
    keys_to_update_in_properties2 = {}
    for key, value in normalized_schema1.items():
        if not key in normalized_schema2:
            print("missing key", key)
        if value != normalized_schema2[key]:
            print("different values", key)
            print(value)
            print(normalized_schema2[key])
            keys_to_update_in_properties2[key] = value["items"]
    if ignore_tuple_type_hints:
        for key, value in keys_to_update_in_properties2.items():
            print("updating key", key, "items from", properties2[key]["items"], "to", value)
            properties2[key]["items"] = value
    if normalize_schema(
        properties1, reference_schemas=reference_schemas
    ) != normalize_schema(properties2, reference_schemas=reference_schemas):
        return False

    # Compare required fields
    required1 = sorted(schema1.get("required", []))
    required2 = sorted(schema2.get("required", []))

    if required1 != required2:
        return False

    return True


def compare_references(
    schema1: Dict[str, Any], schema2: Dict[str, Any], reference_schemas: Dict[str, Any]
) -> bool:
    """Compare references between two schemas recursively, checking definitions."""
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


def compare_schemas(
    schema1: Dict[str, Any],
    schema2: Dict[str, Any],
    reference_schemas: Optional[Dict[str, Any]] = None,
    ignore_tuple_type_hints: bool = False,
) -> bool:
    """Compare two JSON schemas recursively, including properties, references, and required fields."""
    if not reference_schemas:
        reference_schemas = {}
        reference_schemas.update(copy.deepcopy(schema1.get("$defs", {})))
        reference_schemas.update(copy.deepcopy(schema2.get("$defs", {})))

    normalized_schema1 = normalize_schema(schema1, reference_schemas=reference_schemas)
    normalized_schema2 = normalize_schema(schema2, reference_schemas=reference_schemas)

    if normalized_schema1.get("type") != normalized_schema2.get("type"):
        return False

    if not compare_properties(
        normalized_schema1, normalized_schema2, reference_schemas=reference_schemas, ignore_tuple_type_hints=ignore_tuple_type_hints
    ):
        return False

    if not compare_references(
        normalized_schema1, normalized_schema2, reference_schemas
    ):
        return False

    return True
