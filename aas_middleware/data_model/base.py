from __future__ import annotations
from typing import Optional, Dict, Union

from pydantic import BaseModel, validator, root_validator

# TODO: check if reference is working like this
Reference = Union[str]


class Referable(BaseModel):
    """
    Base class for all referable classes. A Referable is an object with a local id (id_short) and a description.

    Args:
        id_short (str): Local id of the object.
        description (str, optional): Description of the object. Defaults to None.
    """
    id_short: str
    description: Optional[str]

    @validator("description", always=True)
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

    @root_validator(pre=True)
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

    @validator("semantic_id", always=True)
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
