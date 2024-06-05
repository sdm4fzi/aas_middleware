from __future__ import annotations

from typing import Literal, Optional, List
from enum import Enum

from pydantic import conlist

from aas_middleware.model.formatting.aas.aas_model import AAS, Submodel, SubmodelElementCollection


class ProcessInformation(Submodel):
    """
    The SubmodelElementCollection GeneralInfo contains 4 SubmodelElements that allow to describe one specific process attribute in a structured, self-describing and interoperable way.
    The types are defined by DIN 8580 for Manufacturing Processes, VDI 2411 for Material Flow Processes, VDI 2243 for Remanufacturing Processes and VDI 2860 for Assembly.

    Args:
        id (str): The id of the general info.
        description (Optional[str]): The description of the process.
        id_short (Optional[str]): The short id of the process.
        semantic_id (Optional[str]): The semantic id of the process.
        general_type (Literal["Manufacturing", "Material Flow", "Remanufacturing", "Assembly", "Other"]): The general type of process or procedure that is describeded by this attribute.
        manufacturing_process_type (Optional[Literal["Primary Shaping", "Forming", "Cutting", "Joining", "Coating", "Changing Material Properties"]]): The type of manufacturing process according to DIN 8580.
        material_flow_process_type (Optional[Literal["Storage", "Handling", "Conveying"]]): The type of material flow process according to VDI 2411.
        remanufacturing_process_type (Optional[Literal["Disassembly", "Remediation", "Cleaning", "Inspection"]]): The type of remanufacturing process according to VDI 2243.
        assembly_process_type (Optional[Literal["Joining", "Handling", "Adjusting", "Testing", "Special Operations"]]): The type of assembly process according to VDI 2860.
    """

    general_type: Literal[
        "Manufacturing", "Material Flow", "Remanufacturing", "Assembly"
    ]
    manufacturing_process_type: Optional[Literal[
        "Primary Shaping",
        "Forming",
        "Cutting",
        "Joining",
        "Coating",
        "Changing Material Properties",
    ]]
    material_flow_process_type: Optional[Literal["Storage", "Handling", "Conveying"]]
    remanufacturing_process_type: Optional[Literal[
        "Disassembly", "Remediation", "Cleaning", "Inspection"
    ]]
    assembly_process_type: Optional[Literal[
        "Joining", "Handling", "Adjusting", "Testing", "Special Operations"
    ]]


class AttributePredicate(SubmodelElementCollection):
    """
    The SubmodelElementCollection “AttributePredicate” contains 4 SubmodelElements that allow to describe one specific process attribute in a structured, self-describing and interoperable way.

    Args:
        description (Optional[str]): The description of the attribute predicate.
        id_short (Optional[str]): The short id of the attribute predicate.
        semantic_id (Optional[str]): The semantic id of the attribute predicate.
        attribute_carrier (str): Semantic reference to the general type of process or procedure that is describeded by this attribute, e.g. a semantic reference to a milling process definition.
        general_attribute (str): Describes semantically the type of attribute that is specified for the attribute carrier, e.g. rotation speed.
        predicate_type (str): Describes semantically what is specified by the value and how to compare it, e.g. requires_to_be, equals, within_range, ....
        attribute_value (str): Describes value of the attribute that is specified for.
    """

    attribute_carrier: str
    general_attribute: str
    predicate_type: str
    attribute_value: str


class ProcessAttributes(Submodel):
    """
    The SubmodelElementCollection “ProcessAttributes” contains 4 SubmodelElements that allow to describe one specific process attribute in a structured, self-describing and interoperable way.

    Args:
        id (str): The id of the process attributes.
        description (Optional[str]): The description of the process attributes.
        id_short (Optional[str]): The short id of the process attributes.
        semantic_id (Optional[str]): The semantic id of the process attributes.
        process_attributes (List[AttributePredicate]): The process attributes of the process (e.g. rotation speed, ...)
    """

    process_attributes: List[AttributePredicate]


class ProcessModelType(str, Enum):
    """
    Enum to describe the type of process model.
    """

    SINGLE_PROCESS = "Single"
    SEQUENTIAL_PROCESS_MODEL = "Sequential"
    GRAPH_PROCESS_MODEL = "Graph"


class ProcessModel(Submodel):
    """
    The SubmodelElementCollection “ProcessModel” contains 4 SubmodelElements that allow to describe one specific process attribute in a structured, self-describing and interoperable way.

    Args:
        id (str): The id of the process model.
        description (Optional[str]): The description of the process model.
        id_short (Optional[str]): The short id of the process model.
        semantic_id (Optional[str]): The semantic id of the process model.
        type_ (ProcessModelType): The type of the process model.
        sequence (Optional[List[str]]): The sequence of the process model (for Sequential process model type) with ids of the subprocesses.
        nodes (Optional[List[str]]): The nodes of the process model (for Graph process model type) with ids of the subprocesses.
        edges (Optional[List[Tuple[str, str]]]): The edges of the process model (for Graph process model type) with ids of the subprocesses.
    """

    type_: ProcessModelType
    sequence: Optional[List[str]]
    nodes: Optional[List[str]]
    edges: Optional[List[conlist(str, min_length=2, max_length=2)]]


class Process(AAS):
    """
    Class to describe a process that is required to produce a product. A process can comprise of multiple sub-processes, described by the process model. With the process attributes, it is specified which attributes are relevant for the process to generate the required transformations of a product.

    Args:
        id (str): The id of the process.
        description (Optional[str]): The description of the process.
        id_short (Optional[str]): The short id of the process.
        general_Info (GeneralInfo): The general information of the process (e.g. type of process, ...)
        process_model (ProcessModel): The process model of the process (e.g. sequence of sub-processes, ...)
        process_attributes (ProcessAttributes): The process attributes of the process (e.g. rotation speed, ...)
    """

    process_information: ProcessInformation
    process_model: ProcessModel
    process_attributes: ProcessAttributes
