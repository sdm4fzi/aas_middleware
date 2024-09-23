from __future__ import annotations
from datetime import datetime
from enum import Enum
from typing import Annotated, TypeVar, Any
from uuid import UUID

from pydantic import BaseModel, BeforeValidator, model_validator


Identifier = TypeVar("Identifier", bound=str | int | UUID)
Reference = TypeVar("Reference", bound=str | int | UUID)
UnIdentifiable = (
    str | int | float | bool | None | UUID | Enum | list | tuple | set | type | datetime
)


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
        return {"id": potential_id}


from aas_middleware.model.util import get_id
