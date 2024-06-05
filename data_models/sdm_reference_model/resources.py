from __future__ import annotations
from typing import List, Optional, Tuple, Literal, Union
from enum import Enum

from pydantic import conlist

from aas_middleware.model.formatting.aas.aas_model import AAS, Submodel, SubmodelElementCollection
from data_models.sdm_reference_model.product import ConstructionData
from data_models.sdm_reference_model.performance import Performance

class ResourceInformation(Submodel):
    """
    Submodel to describe the general information of a resource.

    Args:
        id (str): The id of the general information.
        description (Optional[str]): The description of the general information.
        id_short (Optional[str]): The short id of the general information.
        semantic_id (Optional[str]): The semantic id of the general information.
        manufacturer (Optional[str]): The manufacturer of the resource.
        production_level (Literal["Module", "Station", "System", "Plant", "Network"]): The production level of the resource.
        resource_type (Literal["Manufacturing", "Material Flow", "Storage"]): The type of the resource.
    """
    manufacturer: Optional[str]
    production_level: Literal["Module", "Station", "System", "Plant", "Network"]
    resource_type: Literal["Manufacturing", "Material Flow", "Storage", "Barrier", "Empty Spot", "Source", "Sink"]


class Capabilities(Submodel):
    """
    Submodel to describe the capabilities of a resource by describing available 
    procedures in the resource. 

    Args:
        id (str): The id of the capabilities.
        description (Optional[str]): The description of the capabilities.
        id_short (Optional[str]): The short id of the capabilities.
        semantic_id (Optional[str]): The semantic id of the capabilities.
        procedure_ids (List[str]): The list of ids of procedure that are available for the resource.
    """
    procedures_ids: List[str]


class ControlLogic(Submodel):
    """
    Submodel to describe the control logic of a resource, by describing its control policy. It specifies in which sequence the resource processes the products.

    Args:
        id (str): The id of the control logic.
        id_short (str): The short id of the control logic.
        description (Optional[str]): The description of the control logic.
        semantic_id (Optional[str]): The semantic id of the control logic.
        sequencing_policy (Literal["FIFO", "SPT_transport", "LIFO", "SPT", "EDD", "ODD"]): The sequencing policy of the resource, determining in which sequence requests are processed.
        routing_policy (Literal["random", "nearest", "shortest_queue", "alternating, "round_robin"]): The routing policy of the resource how redundant sub resources are used.
    """
    sequencing_policy: Optional[Literal["FIFO", "SPT", "LIFO", "SPT", "EDD", "ODD"]]
    routing_policy: Optional[Literal["random", "nearest", "shortest_queue", "alternating", "round_robin"]]

class SubResource(SubmodelElementCollection):
    """
    SubmodelElementCollection to describe a subresource of a resource with reference to its AAS, position and orientation (2D or 3D).

    Args:
        description (Optional[str]): The description of the subresource.
        id_short (Optional[str]): The short id of the subresource.
        semantic_id (Optional[str]): The semantic id of the subresource.
        resource_id (str): The id of the subresource.
        position (conlist(float, min_items=2, max_items=3)): The position of the subresource (x, y, z).
        orientation (conlist(float, min_items=1, max_items=3)): The orientation of the subresource (alpha, beta, gamma).
    """

    resource_id: str
    position: conlist(float, min_length=2, max_length=3)
    orientation: conlist(float, min_length=1, max_length=3)


class ResourceConfiguration(Submodel):
    """
    Submodel to describe the configuration of a resource, by describing its sub resources and their position and orientation.

    Args:
        id (str): The id of the resource hierarchy.
        description (Optional[str]): The description of the resource hierarchy.
        id_short (Optional[str]): The short id of the resource hierarchy.
        semantic_id (Optional[str]): The semantic id of the resource hierarchy.
        sub_resources (Optional[List[SubResource]]): IDs ob sub resources
    """
    sub_resources: Optional[List[SubResource]]


class InformationInterface(SubmodelElementCollection):
    """
    Interface for information exchange with the resource.

    Args:
        protocol (str): The protocol of the information interface.
        adress (str): The adress of the information interface (e.g. IP adress)
        port (Optional[int]): The port of the information interface.
    """

    protocol: str
    adress: str
    port: Optional[int]


class MaterialDirectionType(str, Enum):
    """
    Enum to describe the direction of material flow in a material interface.
    """
    IN = "IN"
    OUT = "OUT"
    INOUT = "INOUT"


class MaterialInterface(SubmodelElementCollection):
    """
    Interface for material handling, e.g. if a product is passed to this resource, the MaterialInterface specifies the requried position and orientation
    of the product (each in 2D or 3D coordinates).

    Args:
        position (conlist(float, min_items=2, max_items=3)): The position of the material interface.
        orientation (conlist(float, min_items=2, max_items=3)): The orientation of the material interface.
    """

    position: conlist(float, min_length=2, max_length=3)
    orientation: conlist(float, min_length=2, max_length=3)
    direction: MaterialDirectionType = MaterialDirectionType.INOUT


class EnergyInterface(SubmodelElementCollection):
    """
    Interface for energy handling, e.g. if a product is passed to this resource, the EnergyInterface specifies the requried energy level.

    Args:
        voltage (float): The voltage of the energy interface.
        current (float): The current of the energy interface.
        power (float): The power of the energy interface.
        current_type (str): The current type of the energy interface.
    """

    voltage: float
    current: float
    nominal_power_consumption: float
    peak_power_consumption: float
    standby_power_consumption: float
    current_type: str


class ResourceInterfaces(Submodel):
    """
    Submodel to describe the interfaces of a resource to connect to the resource either by energy, information or material.

    Args:
        id (str): The id of the resource interfaces.
        description (Optional[str]): The description of the resource interfaces.
        id_short (Optional[str]): The short id of the resource interfaces.
        semantic_id (Optional[str]): The semantic id of the resource interfaces.
        information_interface (Optional[List[CommunicationInterface]]): The communication interfaces of the resource.
        material_interfaces (Optional[List[MaterialInterface]]): The material interfaces of the resource.
        energy_interfaces (Optional[List[EnergyInterface]]): The energy interfaces of the resource.
    """

    information_interface: Optional[List[InformationInterface]]
    material_interfaces: Optional[List[MaterialInterface]]
    energy_interfaces: Optional[List[EnergyInterface]]


class ResourcePerformance(SubmodelElementCollection):
    """
    Submodel to make a reference to the Peroformance of a resource.

    Args:
        description (Optional[str]): The description of the resource performance.
        id_short (Optional[str]): The short id of the resource performance.
        semantic_id (Optional[str]): The semantic id of the resource performance.
        performance_id (Optional[str]): The id of the performance AAS of the resource.
        associated_configuration_id (Optional[str]): The id of the configuration AAS of the resource.
        obtained_performance_from (str): The tool / software used to obtain the results.
    """
    performance_id: Optional[str] # link to the performance AAS of the resource
    associated_configuration_id: Optional[str]
    obtained_performance_from: str # Tool / Software used to obtain the results

class ResourcePerformances(Submodel):
    """
    Submodel to describe the performance of a resource.

    Args:
        id (str): The id of the resource performance.
        description (Optional[str]): The description of the resource performance.
        id_short (Optional[str]): The short id of the resource performance.
        semantic_id (Optional[str]): The semantic id of the resource performance.
        resource_performance (Optional[List[ResourcePerformance]]): The performances of the resource.
    """
    resource_performance: Optional[List[ResourcePerformance]]


class ProductReference(Submodel):
    """
    Submodel to describe the emission of a resource.

    Args:
        name (str): Name of the tool that is used for a process.
    """
    product_reference_id: Optional[str] = None  

class Resource(AAS):
    """
    AAS to describe a resource.

    Args:
        id (str): The id of the resource.
        description (Optional[str]): The description of the resource.
        id_short (Optional[str]): The short id of the resource.
        resource_information (Optional[ResourceInformation]): some general information describing the resource.
        capabilities (Optional[Capabilities]): The capabilities of the resource, containing information about available procedures.
        construction_data (Optional[ConstructionData]): The construction data of the resource.
        resource_configuration (Optional[ResourceHierarchy]): The configruation of the resource, containting information about sub resources.
        control_logic (Optional[ControlLogic]): The control logic of the resource.
        resource_interface (Optional[ResourceInterfaces]): the interfaces of the resource.
    """
    resource_information: Optional[ResourceInformation]
    capabilities: Optional[Capabilities]
    construction_data: Optional[ConstructionData]
    resource_configuration: Optional[ResourceConfiguration]
    control_logic: Optional[ControlLogic]
    resource_interface: Optional[ResourceInterfaces]
    resource_performances: Optional[ResourcePerformances]
    product_reference: Optional[ProductReference]
