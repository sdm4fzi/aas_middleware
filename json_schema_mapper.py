from multiprocessing.managers import BaseManager
import typing
from attr import field
from pydantic import BaseModel, create_model, ValidationError, field_validator
from typing import Callable, Dict, List, Optional, Tuple, Type
from datetime import datetime


def get_properties(schema: dict, model_name: str) -> dict:
    """
    Returns the json schema properties of a model in the json schema with a Title that matches the model_name.
    """
    if schema["title"] == model_name:
        return schema["properties"]
    for name, definition in schema["$defs"].items():
        if definition["title"] == model_name:
            assert name == model_name
            return definition["properties"]
        

def get_required_properties(schema: dict, model_name: str) -> List[str]:
    """
    Returns the required properties of a model in the json schema with a Title that matches the model_name.
    """
    if schema["title"] == model_name:
        return schema.get("required", [])
    for name, definition in schema["$defs"].items():
        if definition["title"] == model_name:
            assert name == model_name
            return definition.get("required", [])
    raise ValueError(f"Model {model_name} not found in JSON schema.")
        
def get_type_information_for_list(definition: dict, schema: dict) -> Tuple[Type, ...]:
    """
    Get the type information for a list field in the JSON schema.
    """
    if "$ref" in definition["items"]:
        contained_model = get_pydantic_model_from_schema(schema, definition["items"]["$ref"].split("/")[-1])
        return (List[contained_model], ...)
    if definition["items"].get("type") == "object":
        contained_model = get_pydantic_model_from_schema(schema, definition["items"].get("title"))
        return (List[contained_model], ...)
    else:
        prop_type = convert_type(definition["items"].get("type"))
        return (List[prop_type], ...)
    

def get_pydantic_model_from_schema(schema: dict, model_name: Optional[str]=None) -> Type[BaseModel]:
    """
    Get the type information for each field in the JSON schema.
    """
    if not model_name:
        model_name = schema["title"]
    properties = get_properties(schema, model_name)
    required_properties = get_required_properties(schema, model_name)

    type_information = {}
    # TODO: improve handling of required values (if not set type optional)
    # TODO: also consider enums and unions
    for prop, definition in properties.items():
        if "$ref" in definition:
            print("Reference found", prop, definition["$ref"])
            contained_model = get_pydantic_model_from_schema(schema, definition["$ref"].split("/")[-1])
            type_information[prop] = (contained_model, ...)
        elif definition.get("type") == "object":
            print("Object found", prop)
            contained_model = get_pydantic_model_from_schema(schema, definition.get("title"))
            type_information[prop] = (contained_model, ...)
        elif definition.get("type") == "array":
            print("Array found", prop)
            type_information[prop] = get_type_information_for_list(definition, schema)
        else:
            prop_type = convert_type(definition.get("type"))
            if prop in required_properties:
                type_information[prop] = (prop_type, ...)
            else:
                type_information[prop] = (prop_type, None)
    return create_model(model_name, **type_information)


def convert_type(type_str: str) -> type:
    """
    Converts a type string to its corresponding Python type.
    """
    type_mapping = {
        "string": str,
        "integer": int,
        "number": float,
        "boolean": bool,
        # "array": list,
        # "object": dict,
        # Add more mappings as needed
    }
    return type_mapping.get(type_str, str)  # Default to string if type is unknown


def username_alphanumeric(cls, v):
    assert v.isalnum(), "must be alphanumeric"
    return v


def convert_to_date(cls, v, date_format="%Y-%m-%d"):
    try:
        if isinstance(v, str):
            datetime.strptime(v, date_format)  # Check if the field is in date format
            return datetime.strptime(
                v, date_format
            ).date()  # Convert to another format if needed
        else:
            raise ValueError("Field is not a string")
    except ValueError as e:
        raise ValueError(f"Error converting field to date: {e}")


import aas_middleware


class BillOfMaterialInfo(aas_middleware.SubmodelElementCollection):
    manufacterer: str
    product_type: str


class BillOfMaterial(aas_middleware.Submodel):
    components: typing.List[str]
    bill_of_material_info: BillOfMaterialInfo


class ProcessModel(aas_middleware.Submodel):
    processes: typing.List[str]


class Product(aas_middleware.AAS):
    bill_of_material: BillOfMaterial
    process_model: ProcessModel


json_schema = Product.model_json_schema()
import json
# print(json.dumps(json_schema, indent=4))
# Create dynamic Pydantic model
DynamicModel = get_pydantic_model_from_schema(
    json_schema,
    # property_validators={"name": username_alphanumeric, "dob": convert_to_date}
)

json_data = {
    "id_short": "example_product_id",
    "description": "Example Product",
    "id": "example_product_id",
    "bill_of_material": {
        "id_short": "example_bom_id",
        "description": "Example Bill of Material",
        "id": "example_bom_id",
        "semantic_id": "",
        "components": ["component_1", "component_2"],
        "bill_of_material_info": {
            "id_short": "example_bom_info_id",
            "description": "Example Bill of Material Info",
            "semantic_id": "",
            "manufacterer": "Example Manufacterer",
            "product_type": "Example Product Type",
        },
    },
    "process_model": {
        "id_short": "example_process_model_id",
        "description": "Example Process Model",
        "id": "example_process_model_id",
        "semantic_id": "",
        "processes": ["process_1", "process_2"],
    },
}


try:
    instance = DynamicModel.model_validate(json_data)  # Works with date in correct format
    assert instance.dict() == json_data
    print(instance)
except ValidationError as e:
    print(e)