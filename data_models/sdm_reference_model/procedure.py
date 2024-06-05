from __future__ import annotations
from typing import Literal, Union, Optional, List

from enum import Enum

from aas_middleware.model.formatting.aas.aas_model import AAS, Submodel, SubmodelElementCollection
from data_models.sdm_reference_model.processes import ProcessAttributes
from data_models.sdm_reference_model.distribution import ABSTRACT_REAL_DISTRIBUTION, DistributionTypeEnum

ProcessAttributes.update_forward_refs()


class ProcedureTypeEnum(str, Enum):
    """
    Enum to describe the type of a procedure.
    """
    PRODUCTION = "Production"
    TRANSPORT = "Transport"
    LOADING = "Loading"
    SETUP = "Setup"
    BREAKDOWN = "Breakdown"
    MAINTENANCE = "Maintenance"
    STAND_BY = "StandBy"
    WAITING = "Waiting"
    OFF = "Off"
    NON_SCHEDULED = "NonScheduled"
    ORDER_RELEASE = "OrderRelease"
    ORDER_SHIPPING = "OrderShipping"




class ActivityTypeEnum(str, Enum):
    """
    Enum to describe the type of an activity.
    """
    START = "Start"
    END = "End"
    START_INTERUPT = "StartInterupt"
    END_INTERUPT = "EndInterupt"


class Event(SubmodelElementCollection):
    """
    The Event class represents an event in the execution of a procedure. It contains the time of the event, the resource that executed the event, the procedure that was executed, the activity that was executed, the product that was produced, and whether the event was successful or not.

    Args:
        time (float): The time of the event.
        resource_id (str): The id of the resource that executed the event.
        procedure_id (str): The id of the procedure that was executed.
        procedure_type (ProcedureTypeEnum): The type of the procedure that was executed.
        activity (str): The activity that was executed.
        product_id (Optional[str]): The id of the product that was produced.
        expected_end_time (Optional[float]): The expected end time of the event.
        actual_end_time (Optional[float]): The actual end time of the event.
        success (Optional[bool]): Whether the event was successful or not.
    """
    time: str
    resource_id: str
    procedure_id: str
    procedure_type: ProcedureTypeEnum
    activity: ActivityTypeEnum
    product_id: Optional[str]
    expected_end_time: Optional[str]
    actual_end_time: Optional[str]
    success: Optional[bool]


class ExecutionModel(Submodel):
    """
    The ExecutionModel represents all planned (scheduled) and performed (executed) execution of a process. It contains the schedule of the process, and the execution log of the process.

    Args:
        id (str): The id of the execution model.
        description (Optional[str]): The description of the execution model.
        id_short (Optional[str]): The short id of the execution model.
        semantic_id (Optional[str]): The semantic id of the execution model.
        schedule (List[Event]): The schedule of the procedure.
        exeuction_log (List[Event]): The execution log of the procedure.        
    """
    schedule: Optional[List[Event]]
    exeuction_log: Optional[List[Event]]

class TimeModel(Submodel):
    """
    Submodel containing parameters to represent the timely duration of a procedure.

    Args:
        id (str): The id of the time model.
        description (Optional[str]): The description of the time model.
        id_short (Optional[str]): The short id of the time model.
        semantic_id (Optional[str]): The semantic id of the time model.
        type_ (Literal["sequential", "distribution", "distance_based"]): The type of the time model.
        sequence (Optional[List[float]]): The sequence of timely values (only for sequential time models).
        repeat (Optional[bool]): Whether the sequence is repeated or not (only for sequential time models).
        distribution_type (Optional[str]): The name of the distribution (e.g. "normal", "exponential", "weibull", "lognormal", "gamma", "beta", "uniform", "triangular", "discrete") (only for distribution time models).
        distribution_parameters (Optional[List[float]]): The parameters of the distribution (1: location, 2: scale, 3 and 4: shape) (only for distribution time models).
        speed (Optional[float]): The speed of the resource (only for distance-based time models).
        reaction_time (Optional[float]): The reaction time of the resource (only for distance-based time models).
        acceleration (Optional[float]): The acceleration of the resource (only for distance-based time models).
        deceleration (Optional[float]): The deceleration of the resource (only for distance-based time models).
    """
    type_: Literal["sequential", "distribution", "distance_based"]
    sequence: Optional[List[float]]
    repeat: Optional[bool]
    distribution_type: Optional[DistributionTypeEnum]
    distribution_parameters: Optional[ABSTRACT_REAL_DISTRIBUTION]
    speed: Optional[float]
    reaction_time: Optional[float]
    acceleration: Optional[float]
    deceleration: Optional[float]

class ProcedureInformation(Submodel):
    """
    Submodel containing general information about the procedure.

    Args:
        procedure_type (ProcedureTypeEnum): The type of the procedure.
    """
    procedure_type: ProcedureTypeEnum


class GreenHouseGasEmission(SubmodelElementCollection):
    """
    Submodel collection containing information about the greenhouse gas emission of a procedure in kilogram of CO2-equivalents. 

    Args:
        emission_scope_one (Optional[float]): The greenhouse gas emission of scope 1.
        emission_scope_two (Optional[float]): The greenhouse gas emission of scope 2.
        emission_scope_three (Optional[float]): The greenhouse gas emission of scope 3.
    """
    emission_scope_one: Optional[float]
    emission_scope_two: Optional[float]
    emission_scope_three: Optional[float]

class ProcedureEmission(Submodel):
    """
    Submodel containing the specification of a procedure.

    Args:
        power_consumption (Optional[float]): The power consumption of the procedure.
        green_house_gas_emission (Optional[GreenHouseGasEmission]): The greenhouse gas emission of the procedure.
    """
    power_consumption: Optional[float]
    green_house_gas_emission: Optional[GreenHouseGasEmission]

class Procedure(AAS):
    """
    The Procedure class represents a procedure that is executed by a resource. It contains the process 
    attributes, the execution model, and the time model of the procedure. 

    Args:
        id (str): The id of the procedure.
        description (Optional[str]): The description of the procedure.
        id_short (Optional[str]): The short id of the procedure.
        process_attributes (processes.ProcessAttributes): Parameters that describe what the procedure does and how it does it.
        execution (ExecutionModel): The execution model of the procedure containing planned and performed executions of this procedure.
        time_model (TimeModel): The time model of the procedure containing parameters to represent the timely duration of the procedure.

    """
    procedure_information: ProcedureInformation
    process_attributes: Optional[ProcessAttributes]
    execution_model: Optional[ExecutionModel]
    time_model: Optional[TimeModel]
    procedure_emission: Optional[ProcedureEmission]

