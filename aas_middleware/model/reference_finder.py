from __future__ import annotations

from types import NoneType
from typing import List, Optional, Set, Tuple, Type, Union
import typing
from pydantic import BaseModel, ConfigDict
from enum import Enum

from aas_middleware.model.core import Identifiable
from aas_middleware.model.schema_util import get_all_contained_schemas, get_attribute_dict_of_schema
from aas_middleware.model.util import (
    get_all_contained_identifiables,
    get_id_with_patch,
    get_identifiable_types,
    get_reference_name,
    get_referenced_ids_of_model,
    get_identifiable_attributes_of_model,
    get_unidentifiable_attributes_of_model,
    is_identifiable_container,
    is_identifiable_type,
    is_identifiable_type_container,
)


class ReferenceType(Enum):
    """
    Enum for the reference types. There exist three types of references:
    - Association: The reference is done by an association between two objects, where the model has the referenced object as an attribute.
    - Reference: The reference element is an object and the reference in the model is done by referencing the id of the referenced object.
    - Attribute: The referenced element is an primitive attribute of the model.
    """
    ASSOCIATION = "association"
    REFERENCE = "reference"
    ATTRIBUTE = "attribute"


class ReferenceInfo(BaseModel):
    """
    Object reference to a model in the data model.

    Args:
        identifiable_id (str): The id of the identifiable.
        reference_id (str): The id of the referenced identifiable.
        reference_type (ReferenceType): The type of the reference.
    """

    identifiable_id: str
    reference_id: str
    reference_type: ReferenceType

    model_config = ConfigDict(frozen=True)


def get_reference_infos_of_model(model: Identifiable) -> Set[ReferenceInfo]:
    """
    Method to add information about referencing model ids of the input model.

    Args:
        model (Referable): The model to add the information for.

    Returns:
        Set[ReferenceInfo]: The list of reference infos.
    """
    reference_infos = set()
    identifiables_of_model = get_identifiable_attributes_of_model(model)
    for identifiable in identifiables_of_model:
        if identifiable == model:
            continue
        reference_info = ReferenceInfo(
            identifiable_id=get_id_with_patch(model),
            reference_id=get_id_with_patch(identifiable),
            reference_type=ReferenceType.ASSOCIATION,
        )
        reference_infos.add(reference_info)
    indirect_references = get_referenced_ids_of_model(model)
    for indirect_reference in indirect_references:
        reference_info = ReferenceInfo(
            identifiable_id=get_id_with_patch(model),
            reference_id=indirect_reference,
            reference_type=ReferenceType.REFERENCE,
        )
        reference_infos.add(reference_info)

    unidentifiable_attributes = get_unidentifiable_attributes_of_model(model)
    for attribute_name, attribute_value in unidentifiable_attributes.items():
        reference_info = ReferenceInfo(
            identifiable_id=get_id_with_patch(model),
            reference_id=f"{attribute_name}={attribute_value}",
            reference_type=ReferenceType.ATTRIBUTE,
        )
        reference_infos.add(reference_info)
    return reference_infos


def get_reference_infos(identifiables: List[Identifiable]) -> Set[ReferenceInfo]:
    """
    Method to get all reference infos of a list of identifiables.

    Args:
        identifiables (List[Identifiable]): The list of identifiables.

    Returns:
        Set[ReferenceInfo]: The list of reference infos.
    """
    reference_infos = set()
    for identifiable in identifiables:
        reference_infos = reference_infos | get_reference_infos_of_model(identifiable)
    return reference_infos


def get_reference_infos_of_schema(schema: Type[Identifiable]) -> Set[ReferenceInfo]:
    """
    Method to add information about referencing schema ids of the input schema.

    Args:
        schema (Type[Identifiable]): The schema to add the information for.

    Returns:
        Set[ReferenceInfo]: The list of reference infos.
    """
    reference_infos = set()
    attribute_dict_of_schema = get_attribute_dict_of_schema(schema)
    for attribute_name, attribute_type in attribute_dict_of_schema.items():
        attribute_types = get_identifiable_types(attribute_type)

        for arg in attribute_types:
            reference_info = get_reference_info_for_schema(schema, attribute_name, arg)
            if not reference_info:
                continue
            reference_infos.add(reference_info)
    return reference_infos


def get_reference_info_for_schema(schema: Type[Identifiable], attribute_name: str, attribute_type: Type[Identifiable]) -> Optional[ReferenceInfo]:
    if is_identifiable_type(attribute_type) or is_identifiable_type_container(attribute_type):
        return ReferenceInfo(
            identifiable_id=schema.__name__,
            reference_id=attribute_type.__name__,
            reference_type=ReferenceType.ASSOCIATION,
        )
    elif get_reference_name(attribute_name, attribute_type):
        return ReferenceInfo(
            identifiable_id=schema.__name__,
            reference_id=get_reference_name(attribute_name, attribute_type),
            reference_type=ReferenceType.REFERENCE,
        )
    else:
        return ReferenceInfo(
            identifiable_id=schema.__name__,
            reference_id=f"{schema.__name__}.{attribute_name}",
            reference_type=ReferenceType.ATTRIBUTE,
        )
    

def patch_references(references: Set[ReferenceInfo], schemas: List[Type[Identifiable]]) -> Set[ReferenceInfo]:
    patched_references = set()
    # FIXME: this is not working properly ---> make case distinctions and resolve them step by step
    schema_names = {schema.__name__.split(".")[-1] for schema in schemas}
    print(schema_names)
    for reference in references:
        if reference.reference_type == ReferenceType.ASSOCIATION:
            continue
        elif reference.reference_type == ReferenceType.ATTRIBUTE:
            for schema_name in schema_names:
                adjusted_reference_id = reference.reference_id.split(".")[-1]
                if adjusted_reference_id in schema_name and len(adjusted_reference_id) > len(schema_name) and not reference.identifiable_id == schema_name:
                    # print(f"Patch reference from {reference.identifiable_id} to {reference.reference_id} to {schema_name}")
                    patched_references.add(
                        ReferenceInfo(
                            identifiable_id=reference.reference_id,
                            reference_id=schema_name,
                            reference_type=ReferenceType.REFERENCE,
                        )
                    )
    
        elif reference.reference_type == ReferenceType.REFERENCE:
            for schema_name in schema_names:
                if reference.reference_id in schema_name and len(reference.reference_id) < len(schema_name) and not reference.identifiable_id == schema_name:
                    # print(f"Patch reference from {reference.identifiable_id} to {reference.reference_id} to {schema_name}")
                    patched_references.add(
                        ReferenceInfo(
                            identifiable_id=reference.reference_id,
                            reference_id=schema_name,
                            reference_type=ReferenceType.REFERENCE,
                        )
                    )

    return references | patched_references



def get_schema_reference_infos(schemas: List[Type[Identifiable]]) -> Set[ReferenceInfo]:
    """
    Method to get all reference infos of a list of schemas.

    Args:
        schemas (List[Type[Identifiable]]): The list of schemas.

    Returns:
        List[ReferenceInfo]: The list of reference infos.
    """
    reference_infos = set()
    for schema in schemas:
        reference_infos = reference_infos | get_reference_infos_of_schema(schema)
    return reference_infos



class ReferenceFinder:
    model: Identifiable
    contained_models: List[Identifiable] = []
    references: List[ReferenceInfo] = []

    contained_schemas: List[Type[Identifiable]] = []
    schema_references: List[ReferenceInfo] = []

    @classmethod
    def find(
        cls, model: Identifiable
    ) -> Tuple[List[Identifiable], Set[ReferenceInfo]]:
        """
        Method to find all contained models (inclusive the model itself) and references in a given model.

        Args:
            model (Identifiable): The model to find contained models and references in.

        Returns:
            Tuple[List[Identifiable], List[ReferenceInfo]]: A tuple containing the list of contained models and the list of references.
        """
        finder = cls()
        finder.model = model
        finder.find_contained_identifiables_and_references()
        return finder.contained_models, finder.references

    def find_contained_identifiables_and_references(self):
        """
        Method to find all contained identifiables (inclusive the model itself) and references in the model.
        """
        self.contained_models = get_all_contained_identifiables(self.model)
        self.references = get_reference_infos(self.contained_models)

    @classmethod
    def find_schema_references(
            cls,
            model: Identifiable,
    ) -> Tuple[List[Identifiable], Set[ReferenceInfo]]:
        """
        Method to find all contained models (inclusive the model itself) and references in a given model.

        Args:
            model (Identifiable): The model to find contained models and references in.

        Returns:
            Tuple[List[Identifiable], List[ReferenceInfo]]: A tuple containing the list of contained models and the list of references.
        """
        finder = cls()
        finder.model = model
        finder.find_contained_schemas_and_references()
        return finder.contained_schemas, finder.schema_references
    
    def find_contained_schemas_and_references(self):
        """
        Method to find all contained identifiables (inclusive the model itself) and references in the model.
        """
        self.contained_schemas = get_all_contained_schemas(self.model)
        self.schema_references = get_schema_reference_infos(self.contained_schemas)
        # FIXME: resolve empty referenced nodes without an associated type -> either find subclasses or classes that contain the referenced name (e.g. "acticePoleHousing" for class "PoleHousing")



