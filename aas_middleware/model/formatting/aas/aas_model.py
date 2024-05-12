from __future__ import annotations

from typing import Annotated, Any, Callable, List, Self

from basyx.aas.model import AssetAdministrationShell, DictObjectStore, Submodel
from pydantic import BaseModel, BeforeValidator, model_validator


BasyxModels = AssetAdministrationShell | Submodel | DictObjectStore

def string_does_start_with_a_character(v: str):
    assert v, "value must not be an empty string"
    assert v[0].isalpha(), "value must start with a character"
    return v

AasIdString = Annotated[str, BeforeValidator(string_does_start_with_a_character)]

class Referable(BaseModel):
    """
    Base class for all referable classes of the AAS meta model. A Referable is an object with a local id (id_short) and a description.

    Args:
        id_short (IdString): Local id of the object.
        description (str): Description of the object. Defaults to None.
    """

    id_short: AasIdString
    description: str = ""


class Identifiable(Referable):
    """
    Base class for all identifiable classes in the AAS Meta model. An Identifiable is a Referable with a global id (id_).

    Args:
        id (str): Global id of the object.
        id_short (str): Local id of the object.
        description (str, optional): Description of the object. Defaults to None.
    """

    id: AasIdString

    @model_validator(mode="before")
    @classmethod
    def check_id_and_id_short(cls, data: Any) -> Any:
        if isinstance(data, BaseModel):
            data = data.model_dump()
        elif not isinstance(data, dict):
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
    Base class for all classes that have semantics of the AAS meta model. Semantics are defined by a semantic id, which reference the semantic definition of the object.

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
    

def is_valid_submodel_element(submodel_element: Any) -> bool:
    if isinstance(submodel_element, PrimitiveSubmodelElement):
        return True
    elif isinstance(submodel_element, SubmodelElementCollection):
        return True
    elif isinstance(submodel_element, list):
        return all(is_valid_submodel_element(element) for element in submodel_element)
    elif isinstance(submodel_element, Operation):
        return True
    try:
        # TODO: maybe try SubmodelELementCOllection.model_validate here instead
        SubmodelElementCollection.model_validate(submodel_element)
    except:
        return False
    

class SubmodelElementCollection(HasSemantics, Referable):
    """
    Base class for all submodel element collections.

    Args:
        id_short (str): Local id of the object.
        description (str, optional): Description of the object. Defaults to None.
        semantic_id (str, optional): Semantic id of the object. Defaults to None.
    """
    @model_validator(mode="after")
    def check_submodel_elements(self) -> Self:
        for field_name in self.model_fields:
            if field_name in ["id", "id_short", "description", "semantic_id"]:
                continue
            assert is_valid_submodel_element(getattr(self, field_name)), f"All attributes of a SubmodelElementCollection must be valid SubmodelElements."
        return self
    

class Operation(HasSemantics, Referable):
    input_variables: List[SubmodelElement]
    output_variables: List[SubmodelElement]
    inoutput_variables: List[SubmodelElement]
    # TODO: add a method that allows definition of an operations from a function
    # TODO: check usage of operations of this is conversion to AAS standard


PrimitiveSubmodelElement = int | float | str | bool
SubmodelElement = PrimitiveSubmodelElement | SubmodelElementCollection | List["SubmodelElement"] | Operation

class Submodel(HasSemantics, Identifiable):
    """
    Base class for all submodels.

    Args:
        id (str): Global id of the object.
        id_short (str): Local id of the object.
        description (str, optional): Description of the object. Defaults to None.
        semantic_id (str, optional): Semantic id of the object. Defaults to None.
    """
    @model_validator(mode="after")
    def check_submodel_elements(self) -> Self:
        for field_name in self.model_fields:
            if field_name in ["id", "id_short", "description", "semantic_id"]:
                continue
            assert is_valid_submodel_element(getattr(self, field_name)), f"All attributes of a Submodel must be valid SubmodelElements."
        return self



