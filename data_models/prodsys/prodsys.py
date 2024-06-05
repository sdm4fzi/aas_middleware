from typing import Any, Optional, Union, List
import uuid


from aas_middleware.model.data_model import DataModel
from prodsys import adapters
from prodsys.models import (
    product_data,
    processes_data,
    resource_data,
    time_model_data,
    sink_data,
    source_data,
    state_data,
    scenario_data,
    performance_data
)


class ProdsysModel(DataModel):

    @property
    def time_model_data(self) -> List[time_model_data.TIME_MODEL_DATA]:
        return self.get_models_of_type(self, time_model_data.TIME_MODEL_DATA)
    
    @property
    def product_data(self) -> List[product_data.ProductData]:
        return self.get_models_of_type(self, product_data.ProductData)
    
    @property
    def processes_data(self) -> List[processes_data.PROCESS_DATA_UNION]:
        return self.get_models_of_type(self, processes_data.PROCESS_DATA_UNION)
    
    @property
    def resource_data(self) -> List[resource_data.RESOURCE_DATA_UNION]:
        return self.get_models_of_type(self, resource_data.RESOURCE_DATA_UNION)
    
    @property
    def sink_data(self) -> List[sink_data.SinkData]:
        return self.get_models_of_type(self, sink_data.SinkData)
    
    @property
    def source_data(self) -> List[source_data.SourceData]:
        return self.get_models_of_type(self, source_data.SourceData)
    
    @property
    def state_data(self) -> List[state_data.StateData]:
        return self.get_models_of_type(self, state_data.StateData)
    
    @property
    def scenario_data(self) -> List[scenario_data.ScenarioData]:
        return self.get_models_of_type(self, scenario_data.ScenarioData)
    
    @property
    def event_data(self) -> List[performance_data.Event]:
        return self.get_models_of_type(self, performance_data.Event)
    @property
    def performance_data(self) -> List[performance_data.Performance]:
        return self.get_models_of_type(self, performance_data.Performance)