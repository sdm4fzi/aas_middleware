from __future__ import annotations
from typing import Optional, Dict, Union, TypeVar
from uuid import UUID

from pydantic import BaseModel, field_validator, model_validator, root_validator

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


class Referable(BaseModel):
    """
    Base class for all referable classes. A Referable is an object with a local id (id_short) and a description.

    Args:
        id_short (str): Local id of the object.
        description (str, optional): Description of the object. Defaults to None.
    """

    id_short: str
    description: Optional[str]

    @field_validator("description")
    def set_default_description(cls, v, values, **kwargs):
        if v is None:
            return ""
        return v


class Identifiable(Referable):
    """
    Base class for all identifiable classes. An Identifiable is a Referable with a global id (id_).

    Args:
        id (str): Global id of the object.
        id_short (str): Local id of the object.
        description (str, optional): Description of the object. Defaults to None.
    """

    id: str

    @model_validator(mode="before")
    def set_default_id_short(cls, values):
        if "id_short" not in values and "id" in values:
            values["id_short"] = values["id"]
            return values
        return values


class HasSemantics(BaseModel):
    """
    Base class for all classes that have semantics. Semantics are defined by a semantic id, which reference the semantic definition of the object.

    Args:
        semantic_id (str, optional): Semantic id of the object. Defaults to None.
    """

    semantic_id: Optional[str]

    @field_validator("semantic_id")
    def set_default_description(cls, v, values, **kwargs):
        if v is None:
            return ""
        return v


class AAS(Identifiable):
    """
    Base class for all Asset Administration Shells (AAS).

    Args:
        id (str): Global id of the object.
        id_short (str): Local id of the object.
        description (str, optional): Description of the object. Defaults to None.
    """

    pass


class Submodel(HasSemantics, Identifiable):
    """
    Base class for all submodels.

    Args:
        id (str): Global id of the object.
        id_short (str): Local id of the object.
        description (str, optional): Description of the object. Defaults to None.
        semantic_id (str, optional): Semantic id of the object. Defaults to None.
    """

    pass


class SubmodelElementCollection(HasSemantics, Referable):
    """
    Base class for all submodel element collections.

    Args:
        id_short (str): Local id of the object.
        description (str, optional): Description of the object. Defaults to None.
        semantic_id (str, optional): Semantic id of the object. Defaults to None.
    """

    pass
