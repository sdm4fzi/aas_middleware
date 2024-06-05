from typing import List, Optional, Tuple, Literal

from enum import Enum

from aas_middleware.model.formatting.aas.aas_model import AAS, Submodel, SubmodelElementCollection
from data_models.sdm_reference_model.procedure import Event

# TODO docstrings are missing


class KPIEnum(str, Enum):
    """
    Defines the KPIs that can be used in the system (based on DIN ISO 22400).
    """
    OUTPUT = "output"
    THROUGHPUT = "throughput"
    COST = "cost"
    WIP = "WIP"

    TRHOUGHPUT_TIME = "throughput_time"
    PROCESSING_TIME = "processing_time"

    PRODUCTIVE_TIME = "productive_time"
    STANDBY_TIME = "standby_time"
    SETUP_TIME = "setup_time"
    UNSCHEDULED_DOWNTIME = "unscheduled_downtime"

    DYNAMIC_WIP = "dynamic_WIP"
    DYNAMIC_THROUGHPUT_TIME = "dynamic_throughput_time"


class KPILevelEnum(str, Enum):
    """
    Defines the levels on which a KPI can be measured.
    """
    SYSTEM = "system"
    RESOURCE = "resource"
    ALL_PRODUCTS = "all_products"
    PRODUCT_TYPE = "product_type"
    PRODUCT = "product"
    PROCESS = "process"

class KPI(SubmodelElementCollection):
    """
    Defines a Key Performance Indicator (KPI) that can be used to describe the performance of the system.

    Args:
        name (KPIEnum): The name of the KPI.
        target (Literal["min", "max"]): The target of the KPI.
        weight (Optional[float], optional): The weight of the KPI. Defaults to 1.
        value (Optional[float], optional): The value of the KPI. Defaults to None.
        context (Optional[Tuple[KPILevelEnum, ...]], optional): The context of the KPI specified by KPI levels to which the KPI applies. Defaults to None.
        resource (Optional[str], optional): The resource to which the KPI applies. Defaults to None.
        product (Optional[str], optional): The product to which the KPI applies. Defaults to None.
        process (Optional[str], optional): The process to which the KPI applies. Defaults to None.
        start_time (Optional[float], optional): The start time of the KPI. Defaults to None.
        end_time (Optional[float], optional): The end time of the KPI. Defaults to None.
    """
    name: KPIEnum
    target: Literal["min", "max"]
    weight: Optional[float] = 1
    value: Optional[float] = None
    context: Optional[Tuple[KPILevelEnum, ...]] = None
    resource: Optional[str] = None
    product: Optional[str] = None
    process: Optional[str] = None
    start_time: Optional[float] = None
    end_time: Optional[float] = None


class KeyPerformanceIndicators(Submodel):
    """
    Defines a collection of Key Performance Indicators (KPIs) that can be used to describe the performance of the system.

    Args:
        kpis (List[KPI]): The list of KPIs.
    """
    kpis: List[KPI]

class EventLog(Submodel):
    """
    Defines a log of events that have occurred in the system.

    Args:
        event_log (List[Event]): The list of events that have occurred in the system.
    """
    event_log: List[Event]

class Performance(AAS):
    """
    AAS to describe the performance of a production system.

    Args:
        key_performance_indicators (KeyPerformanceIndicators): The Key Performance Indicators (KPIs) that describe the performance of the system.
        event_log (Optional[EventLog], optional): A log of events that have occurred in the system. Defaults to None.
    """
    key_performance_indicators: KeyPerformanceIndicators
    event_log: Optional[EventLog]
