
from typing import Literal, Union, Optional, List

from enum import Enum

from aas_middleware.model.formatting.aas.aas_model import AAS, Submodel, SubmodelElementCollection
from data_models.sdm_reference_model.distribution import ABSTRACT_INTEGER_DISTRIBUTION, ABSTRACT_REAL_DISTRIBUTION
from data_models.sdm_reference_model.performance import KPIEnum

class ChangeDriverInfluence(SubmodelElementCollection):
    """
    The ChangeDriverInfluence represents the influence of a change driver on a receptor key figure.

    Args:
        is_influenced (bool): True if the change driver influences the receptor key figure, False otherwise.
        influenecing_change_driver_id (str): The id of the change driver that influences the receptor key figure.
        influence_type (str): The type of the influence of the change driver on the receptor key figure.
        influence_time (float): The time of the influence of the change driver on the receptor key figure.
    """
    is_influenced: bool
    influenecing_change_driver_id: str # ID of the change driver
    influence_type: str # changed to type because boolean diddn't make sense
    influence_time: float # changed to float because boolean didn't make sense for time

    
class ChangeDriver(SubmodelElementCollection):
    """
    The ChangeDriver represents a change driver of a change scenario.

    Args:
        id (str): The id of the change driver.
        description (Optional[str]): The description of the change driver.
        id_short (Optional[str]): The short id of the change driver.
        sematic_id (Optional[str]): The semantic id of the change driver.
        occurrence_distribution_function_over_time_horizon (ABSTRACT_REAL_DISTRIBUTION): The occurrence distribution function over the time horizon.
        occurrence_distribution_per_unit_of_time (ABSTRACT_INTEGER_DISTRIBUTION): The occurrence distribution per unit of time.
        frequency (float): The frequency of the change driver.
        change_driver_influences (List[ChangeDriverInfluence]): The influences of the change driver on the receptor key figures.
        influenced_receptor_key_figure_ids (List[str]): The ids of the receptor key figures that are influenced by the change driver.
    """
    distribution_function_over_time_horizon: ABSTRACT_REAL_DISTRIBUTION # wann der Wandlungstreiber in einem vorgegebenen Zeitraum auftreten kann
    occurrence_distribution_per_unit_of_time: ABSTRACT_INTEGER_DISTRIBUTION # mit welcher Wahrscheinlichkeit der Wandlungstreiber insgesamt eintritt
    frequency: float
    change_driver_influences: List[ChangeDriverInfluence]
    influenced_receptor_key_figure_ids: List[str] # List of IDs of the receptor key figures

class ReceptorEnum(str, Enum):
    QUANTITY= "quantity"
    COST= "cost"
    TIME= "time"
    PRODUCT= "product"
    TECHNOLOGY= "technology"
    QUALITY= "quality"

class ModellingEnum(str, Enum):
    DISCRETE = "discrete"
    CONTINUOUS = "continuous"

class DiscreteRKF(SubmodelElementCollection):
    """
    The DiscreteRKF represents a discrete receptor key figure.

    Args:
        value_for_occurence (str): The value for the occurence of the receptor key figure.
        value_for_non_occurence (str): The value for the non-occurence of the receptor key figure.
        previous_value (str): The previous value of the receptor key figure.
    """
    value_for_occurence: str
    value_for_non_occurence: str
    previous_value: str

class ContinuousRKF(SubmodelElementCollection):
    """
    The ContinuousRKF represents a continuous receptor key figure.

    Args:
        absolute_influences_change_drivers (str): The absolute influences of the change drivers on the receptor key figure.
        relative_influences_change_drivers (str): The relative influences of the change drivers on the receptor key figure.
        slope_influences_change_drivers (str): The slope influences of the change drivers on the receptor key figure.
        previous_slope (float): The previous slope of the receptor key figure.
        previous_value (float): The previous value of the receptor key figure.
    """
    absolute_influences_change_drivers: str 
    relative_influences_change_drivers: str
    slope_influences_change_drivers: str
    previous_slope: float
    previous_value: float

class ReceptorKeyFigure(SubmodelElementCollection):
    receptor_type: ReceptorEnum
    modelling_type: ModellingEnum
    unit: str
    value: Union[DiscreteRKF, ContinuousRKF]

class ScenarioModel(Submodel):
    change_drivers: List[ChangeDriver]
    receptor_key_figures: List[ReceptorKeyFigure]

class ReconfigurationConstraints(Submodel):
    """
    The ReconfigurationConstraints represents the constraints for the reconfiguration of the production system.

    Args:
        max_reconfiguration_cost (float): The maximum cost of reconfiguration of the production system.
        max_reconfiguration_time (float): The maximum time of reconfiguration of the production system.
        max_number_of_machines (int): The maximum number of machines of the production system.
        max_number_of_transport_resources (int): The maximum number of transport resources of the production system.
        max_number_of_process_model_per_resource (int): The maximum number of process models per resource of the production system.
    """
    max_reconfiguration_cost: float
    max_reconfiguration_time: float
    max_number_of_machines: int
    max_number_of_transport_resources: int
    max_number_of_process_modules_per_resource: int


class ReconfigurationEnum(str, Enum):
    """
    # from prodsys
    Enum that represents the different levels of reconfigurations that are possible.

    - ProductionCapacity: Reconfiguration of production capacity (number of machines and their configuration)
    - TransportCapacity: Reconfiguration of transport capacity (number of transport resources and their configuration)
    - Layout: Reconfiguration of layout (only position of resources)
    - SequencingLogic: Reconfiguration of sequencing logic (only the control policy of resources)
    - RoutingLogic: Reconfiguration of routing logic (only the routing heuristic of routers)
    """

    FULL = "full"
    PRODUCTION_CAPACITY = "production_capacity"
    TRANSPORT_CAPACITY = "transport_capacity"
    LAYOUT = "layout"
    SEQUENCING_LOGIC = "sequencing_logic"
    ROUTING_LOGIC = "routing_logic"

class ReconfigurationOptions(Submodel):
    """
    The ReconfigurationOptions represents the options for the reconfiguration of the production system.

    Args:
        id (str): The id of the reconfiguration option.
        description (Optional[str]): The description of the reconfiguration option.
        id_short (Optional[str]): The short id of the reconfiguration option.
        sematic_id (Optional[str]): The semantic id of the reconfiguration option.
        reconfiguration_type (ReconfigurationEnum): The type of reconfiguration that is possible.
        machine_controllers (List[Literal["FIFO", "LIFO", "SPT"]]): The machine controllers that are possible.
        transport_controllers (List[Literal["FIFO", "SPT_transport"]]): The transport controllers that are possible.
        routing_heuristics (List[Literal["shortest_queue", "random"]]): The routing heuristics that are possible.
    """
    reconfiguration_type: ReconfigurationEnum
    machine_controllers: List[Literal["FIFO", "LIFO", "SPT"]]
    transport_controllers: List[Literal["FIFO", "SPT_transport"]]
    routing_heuristics: List[Literal["shortest_queue", "random"]]


class Objective(SubmodelElementCollection):
    """
    The Objective represents an objective of the change scenario.

    Args:
        description (Optional[str]): The description of the objective.
        id_short (Optional[str]): The short id of the objective.
        sematic_id (Optional[str]): The semantic id of the objective.
        type (KPIEnum): The type of the objective.
        weight (float): The weight of the objective.
    """
    type: KPIEnum
    weight: float


class ReconfigurationObjectives(Submodel):
    """
    The ReconfigurationObjectives represents the objectives of the change scenario.

    Args:
        id (str): The id of the reconfiguration objectives.
        description (Optional[str]): The description of the reconfiguration objectives.
        id_short (Optional[str]): The short id of the reconfiguration objectives.
        sematic_id (Optional[str]): The semantic id of the reconfiguration objectives.
        objectives (List[Objective]): The objectives of the change scenario.
    """
    objectives: List[Objective]


class ScenarioResources(Submodel):
    """
    The ResourceReferenceSubmodel represents a reference to a resource.

    Args:
        id (str): The id of the resource reference.
        description (Optional[str]): The description of the resource reference.
        id_short (Optional[str]): The short id of the resource reference.
        sematic_id (Optional[str]): The semantic id of the resource reference.
        base_id (str): The id of the base production system.
        solution_ids (List[str]): The ids of the resources that are solutions of the optimization.
    """
    base_id: Optional[str]
    solution_ids: Optional[List[str]]

class ChangeScenario(AAS):
    """
    The ChangeScenario represents a change scenario for the configuration of a production system. It contains the change drivers and the 
    receptor key figures of the change scenario, thus describing how requirements on the production system change over time.

    Moreover, the change scenario holds constraints and options for reconfiguration of the production system, objectives of the change 
    scenario and a list to found solutions. 

    Args:
        id (str): The id of the change scenario.
        description (Optional[str]): The description of the change scenario.
        id_short (Optional[str]): The short id of the change scenario.
    """
    scenario_model: Optional[ScenarioModel]
    scenario_resources: Optional[ScenarioResources]
    reconfiguration_constraints: Optional[ReconfigurationConstraints]
    reconfiguration_options: Optional[ReconfigurationOptions]
    reconfiguration_objectives: Optional[ReconfigurationObjectives]