from __future__ import annotations
from enum import Enum
from typing import Annotated, List, TypeVar, Any
from uuid import UUID
import inspect


from pydantic import BaseModel, BeforeValidator, model_validator


Identifier = TypeVar("Identifier", bound=str | int | UUID)
Reference = TypeVar("Reference", bound=str | int | UUID)


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
    if isinstance(model, str | int | float | bool | None | UUID | Enum | list | tuple | set | type):
        raise ValueError("Model is a basic type and has no id attribute.")
    
    if isinstance(model, BaseModel):
        identifiable_fields = get_identifiable_fields(model)
        if len(identifiable_fields) > 1:
            raise ValueError(f"Model has multiple Identifier attributes: {model}")
        if identifiable_fields:
            return getattr(model, identifiable_fields[0])
    elif hasattr(model, "__dict__"):
        sig = inspect.signature(type(model).__init__)
        potential_identifier = []
        for param in sig.parameters.values():
            if param.annotation is Identifier:
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
    potential_id_attributes = ["id", "id_short", "Id", "ID", "Identifier", "identifier", "Identity", "identity"]
    for id_attribute in potential_id_attributes:
        if id_attribute in data and isinstance(data[id_attribute], str | int | UUID):
            return data[id_attribute]
 
    raise ValueError(f"Model {model} has no attribute that can be used as id attribute.")



# TODO: move these function to the util and use them in the data model
def get_identifiable_fields(model: BaseModel) -> List[str]:
    """
    Function to get the fields of a model that are of type Identifier.

    Args:
        model (BaseModel): A Basemodel that is checked for identifier fields

    Returns:
        List[str]: The field names that are Identifiers
    """
    model_fields = []
    for field_name, field_info in model.model_fields.items():
        if field_info.annotation is Identifier:
            model_fields.append(field_name)
    return model_fields


def get_referable_fields(model: BaseModel):
    model_fields = []
    for field_name, field_info in model.model_fields.items():
        if field_info.annotation is Reference:
            model_fields.append(field_name)
    return model_fields

def string_is_not_empty(v: str):
    assert v, "value must not be an empty string"
    return v

IdString = Annotated[str | int | UUID, BeforeValidator(string_is_not_empty)]


class Identifiable(BaseModel):
    """
    Base class for all identifiable classes that have an identifier, that allows to identify these objects. 

    If no id is set, the id function of the python object is used. Otherwise, a uuid is generated.

    Args:
        id (str): Global id of the object.
    """

    id: IdString

    @model_validator(mode="before")
    @classmethod
    def check_id_and_id_short(cls, data: Any) -> Any:
        potential_id = get_id(data)
        assert potential_id, "Either id or id_short must be set"
        print("_________________Correct assertion")
        return {"id": potential_id}