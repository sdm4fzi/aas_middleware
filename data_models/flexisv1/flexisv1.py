from typing import Any, Optional, Union, List
import uuid

from pydantic import field_validator, model_validator
import pandas as pd

from aas_middleware.model.core import Identifiable
import datetime

from aas_middleware.model.data_model import DataModel



def date_time_string_to_duration(value: str) -> float:
    """
    Convert a string in the format %H:%M:%S.%f to a float in minutes.

    Args:
        value (str): String in the format %H:%M:%S.%f, e.g. 00:00:00.000

    Returns:
        float: Duration in minutes
    """
    if isinstance(value, float):
        return value
    return (datetime.datetime.strptime(value, "%H:%M:%S.%f") - datetime.datetime.strptime("00:00:00", "%H:%M:%S")).total_seconds()


def date_time_string_to_datetime(value: str | datetime.datetime) -> str:
    """
    Convert a string in the format %H:%M:%S.%f to a datetime object.

    Args:
        value (str): String in the format %H:%M:%S.%f, e.g. 2023-06-23 00:00:00.000

    Returns:
        datetime: Datetime object
    """
    if isinstance(value, str):
        if "T" in value:
            return datetime.datetime.fromisoformat(value).isoformat()
        else:
            return datetime.datetime.strptime(value, "%Y-%m-%d %H:%M:%S.%f").isoformat()
    if not isinstance(value, datetime.datetime):
        raise TypeError("value must be of type str or datetime.datetime")
    return value.isoformat()

class SetupTime(Identifiable):
    duration: float
    resource_id: str
    task_from_id: str
    task_to_id: str

    @field_validator("duration", mode="before")
    def duration_to_timedelta(cls, v: Any):
        return date_time_string_to_duration(v)

class ProcessTime(Identifiable):
    duration: float
    resource_id: str
    task_id: str

    @field_validator("duration", mode="before")
    def duration_to_timedelta(cls, v):
        return date_time_string_to_duration(v)

class TransportTime(Identifiable):
    duration: float

    @field_validator("duration", mode="before")
    def duration_to_timedelta(cls, v: pd.Timestamp):
        return date_time_string_to_duration(v)

class Task(Identifiable):
    name: str


class ResourceTask(Identifiable):
    resource_id: str
    task_id: str


class Resource(Identifiable):
    locale: str
    name: str
    resource_type_id: str
    capacity_max: Optional[Union[str, int]]
    parent_id: Optional[str]
    position_id: Optional[str]


class ResourceType(Identifiable):
    name: str

class Position(Identifiable):
    x_coordinate: float
    y_coordinate: float
    angle: float


class ResourceAvailibility(Identifiable):
    resource_id: str
    availibility: float
    mttf: float
    mttr: float

    @field_validator("mttf", mode="before")
    def duration_to_timedelta(cls, v: pd.Timestamp):
        return date_time_string_to_duration(v)

    @field_validator("mttr", mode="before")
    def duration_to_timedelta2(cls, v: pd.Timestamp):
        return date_time_string_to_duration(v)


class ResourceVariant(Identifiable):
    resource_id: str
    cad_file_name: str


class WorkPlan(Identifiable):
    name: str


class WorkPlanTask(Identifiable):
    sequence: int
    task_id: str
    work_plan_id: str

class Job(Identifiable):
    work_plan_id: str
    name: str	
    release_date: str
    due_date: str
    target_date: str

    @field_validator("release_date", mode="before")
    def duration_to_timedelta(cls, v):
        return date_time_string_to_datetime(v)
    
    @field_validator("due_date", mode="before")
    def duration_to_timedelta2(cls, v):
        return date_time_string_to_datetime(v)
    
    @field_validator("target_date", mode="before")
    def duration_to_timedelta3(cls, v):
        return date_time_string_to_datetime(v)

class JobTask(Identifiable):
    job_id: str
    name: str
    sequence: int
    task_id: str


class ScheduledJobTask(Identifiable):
    job_task_id: str
    process_begin_date: str
    process_end_date: str
    resource_id: str
    arrival_date: str
    departure_date: str
    setup_begin_date: str
    teardown_end_date: str

    @model_validator(mode="before")
    def set_id_short(cls, values):
        id_short = "u" + str(uuid.uuid1()).replace("-", "_")
        values["id_short"] = id_short
        return values

    @field_validator("process_begin_date",mode="before")
    def duration_to_timedelta(cls, v):
        return date_time_string_to_datetime(v)
    
    @field_validator("process_end_date",mode="before")
    def duration_to_timedelta2(cls, v):
        return date_time_string_to_datetime(v)
    
    @field_validator("arrival_date",mode="before")
    def duration_to_timedelta3(cls, v):
        return date_time_string_to_datetime(v)
    
    @field_validator("departure_date",mode="before")
    def duration_to_timedelta4(cls, v):
        return date_time_string_to_datetime(v)
    
    @field_validator("setup_begin_date",mode="before")
    def duration_to_timedelta5(cls, v):
        return date_time_string_to_datetime(v)
    
    @field_validator("teardown_end_date",mode="before")
    def duration_to_timedelta6(cls, v):
        return date_time_string_to_datetime(v)

class Scenario(Identifiable):
    reconfiguration_type: str	
    resource_id: str
    max_reconfiguration_cost: float	
    max_number_of_machines: int	
    max_number_of_transport_resources: int
    max_number_of_process_modules_per_resource: int


class FlexisDataModel(DataModel):
    @property
    def setup_times(self) -> List[SetupTime]:
        return self.get_models_of_type(self, SetupTime)
    
    @property
    def process_times(self) -> List[ProcessTime]:
        return self.get_models_of_type(self, ProcessTime)
    
    @property
    def transport_times(self) -> List[TransportTime]:
        return self.get_models_of_type(self, TransportTime)
    
    @property
    def tasks(self) -> List[Task]:
        return self.get_models_of_type(self, Task)
    
    @property
    def resource_tasks(self) -> List[ResourceTask]:
        return self.get_models_of_type(self, ResourceTask)
    
    @property
    def resources(self) -> List[Resource]:
        return self.get_models_of_type(self, Resource)
    
    @property
    def resource_availibilities(self) -> List[ResourceAvailibility]:
        return self.get_models_of_type(self, ResourceAvailibility)
    
    @property
    def resource_variants(self) -> List[ResourceVariant]:
        return self.get_models_of_type(self, ResourceVariant)
    
    @property
    def resource_types(self) -> List[ResourceType]:
        return self.get_models_of_type(self, ResourceType)
    
    @property
    def positions(self) -> List[Position]:
        return self.get_models_of_type(self, Position)
    
    @property
    def work_plans(self) -> List[WorkPlan]:
        return self.get_models_of_type(self, WorkPlan)
    
    @property
    def work_plan_tasks(self) -> List[WorkPlanTask]:
        return self.get_models_of_type(self, WorkPlanTask)
    
    @property
    def scenarios(self) -> List[Scenario]:
        return self.get_models_of_type(self, Scenario)
    
    @property
    def jobs(self) -> List[Job]:
        return self.get_models_of_type(self, Job)
    
    @property
    def job_tasks(self) -> List[JobTask]:
        return self.get_models_of_type(self, JobTask)
    
    @property
    def scheduled_job_tasks(self) -> List[ScheduledJobTask]:
        return self.get_models_of_type(self, ScheduledJobTask)


FLEXIS_TYPES_LIST = [WorkPlanTask, ResourceVariant, ResourceAvailibility, ProcessTime, ResourceTask, SetupTime, TransportTime, Job, JobTask, ScheduledJobTask, Task, Resource, ResourceType, Position, WorkPlan, Scenario]
FLEXIS_TYPES = Union[WorkPlanTask, ResourceVariant, ResourceAvailibility, ProcessTime, ResourceTask, SetupTime, TransportTime, Job, JobTask, ScheduledJobTask, Task, Resource, ResourceType, Position, WorkPlan, Scenario]