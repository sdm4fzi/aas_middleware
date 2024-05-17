from typing import List, Tuple
from pydantic import BaseModel
from enum import Enum

from aas_middleware.model.core import Identifiable
from aas_middleware.model.util import (
    get_all_contained_identifiables,
    get_id_with_patch,
    get_referenced_ids_of_model,
    get_identifiable_attributes_of_model,
)


class ReferenceType(Enum):
    ASSOCIATION = "association"
    REFERENCE = "reference"


class ReferenceInfo(BaseModel):
    """
    Object reference to a model in the data model.

    Args:
    """

    identifiable_id: str
    reference_id: str
    reference_type: ReferenceType


def get_reference_infos_of_model(model: Identifiable) -> List[ReferenceInfo]:
    """
    Method to add information about referencing model ids of the input model.

    Args:
        model (Referable): The model to add the information for.

    Returns:
        List[ReferenceInfo]: The list of reference infos.
    """
    reference_infos = []
    identifiables_of_model = get_identifiable_attributes_of_model(model)
    for identifiable in identifiables_of_model:
        if identifiable == model:
            continue
        reference_info = ReferenceInfo(
            identifiable_id=get_id_with_patch(model),
            reference_id=get_id_with_patch(identifiable),
            reference_type=ReferenceType.ASSOCIATION,
        )
        reference_infos.append(reference_info)
    indirect_references = get_referenced_ids_of_model(model)
    for indirect_reference in indirect_references:
        reference_info = ReferenceInfo(
            identifiable_id=get_id_with_patch(model),
            reference_id=indirect_reference,
            reference_type=ReferenceType.REFERENCE,
        )
        reference_infos.append(reference_info)
    return reference_infos


def get_reference_infos(identifiables: List[Identifiable]) -> List[ReferenceInfo]:
    """
    Method to get all reference infos of a list of identifiables.

    Args:
        identifiables (List[Identifiable]): The list of identifiables.

    Returns:
        List[ReferenceInfo]: The list of reference infos.
    """
    reference_infos = []
    for identifiable in identifiables:
        reference_infos += get_reference_infos_of_model(identifiable)
    return reference_infos


class ReferenceFinder:
    model: Identifiable
    contained_models: List[Identifiable] = []
    references: List[ReferenceInfo] = []

    @classmethod
    def find(
        cls, model: Identifiable
    ) -> Tuple[List[Identifiable], List[ReferenceInfo]]:
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
