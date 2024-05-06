from __future__ import annotations
from typing import Annotated, Any, Optional, Dict, Self, Union, TypeVar
from uuid import UUID

from pydantic import BaseModel, BeforeValidator, field_validator, model_validator, root_validator

Identifier = TypeVar("Identifier", bound=str | int | UUID)
Reference = TypeVar("Reference", bound=str | int | UUID)


# TODO: move these function to the util
def get_identifiable_fields(model: BaseModel):
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

def string_does_start_with_a_character(v: str):
    assert v[0].isalpha(), "value must start with a character"
    return v

IdString = Annotated[str, BeforeValidator(string_is_not_empty), BeforeValidator(string_does_start_with_a_character)]

class Referable(BaseModel):
    """
    Base class for all referable classes. A Referable is an object with a local id (id_short) and a description.

    Args:
        id_short (IdString): Local id of the object.
        description (str): Description of the object. Defaults to None.
    """

    id_short: IdString
    description: str = ""


class Identifiable(Referable):
    """
    Base class for all identifiable classes. An Identifiable is a Referable with a global id (id_).

    Args:
        id (str): Global id of the object.
        id_short (str): Local id of the object.
        description (str, optional): Description of the object. Defaults to None.
    """

    id: IdString

    @model_validator(mode="before")
    @classmethod
    def check_id_and_id_short(cls, data: Any) -> Any:
        if isinstance(data, BaseModel):
            data = data.model_dump()
        elif not isinstance(data, dict):
            # TODO: also make here some validation that similarly named values are renamed...
            data = {
                "id": getattr(data, "id", ""),
                "id_short": getattr(data, "id_short", "")
            }
        assert "id" in data or "id_short" in data, "Either id or id_short must be set"
        if "id_short" not in data:
            data["id_short"] = data["id"]
        if "id" not in data:
            data["id"] = data["id_short"]
        return data

class HasSemantics(BaseModel):
    """
    Base class for all classes that have semantics. Semantics are defined by a semantic id, which reference the semantic definition of the object.

    Args:
        semantic_id (str): Semantic id of the object. Defaults to None.
    """

    semantic_id: str = ""


class AAS(Identifiable):
    """
    Base class for all Asset Administration Shells (AAS).

    Args:
        id (str): Global id of the object.
        id_short (str): Local id of the object.
        description (str, optional): Description of the object. Defaults to None.
    """

    @model_validator(mode="after")
    def check_submodels(self) -> Self:
        for field_name in self.model_fields:
            if field_name in ["id", "id_short", "description"]:
                continue
            assert Submodel.model_validate(getattr(self, field_name)), f"All attributes of an AAS must be of type Submodel or inherit from Submodel"
        return self


class Submodel(HasSemantics, Identifiable):
    """
    Base class for all submodels.

    Args:
        id (str): Global id of the object.
        id_short (str): Local id of the object.
        description (str, optional): Description of the object. Defaults to None.
        semantic_id (str, optional): Semantic id of the object. Defaults to None.
    """
    # TODO: add here a check that all attributes (or attributes in list) validate the SubmodelElementCollection
    # if not primitive
    # TODO: also consider operations as callables...


class SubmodelElementCollection(HasSemantics, Referable):
    """
    Base class for all submodel element collections.

    Args:
        id_short (str): Local id of the object.
        description (str, optional): Description of the object. Defaults to None.
        semantic_id (str, optional): Semantic id of the object. Defaults to None.
    """
    # TODO: add here a check that all attributes (or attributes in list) validate the SubmodelElementCollection
    # if not primitive values
