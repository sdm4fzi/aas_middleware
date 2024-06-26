from __future__ import annotations
from typing import List, Optional

from pydantic import BaseModel, create_model

from aas_middleware.model.data_model import DataModel
from aas_middleware.model.data_model_rebuilder import DataModelRebuilder, get_patched_aas_object
from aas_middleware.model.data_model_visualizer import get_instance_graph, get_type_graph, visualize_graph
from aas_middleware.model.formatting.aas import aas_model
from aas_middleware.model.formatting.aas.basyx_formatter import BasyxFormatter
from aas_middleware.model.reference_finder import ReferenceType

# TODO: use something like this to create tests for this...

class Child(BaseModel):
    Id: str
    age: int

class NameInfo(BaseModel):
    first_name: str
    last_name: str

class Parent(BaseModel):
    Id: str
    name: NameInfo
    child: Child

name_info_child = NameInfo(first_name="Peter", last_name="Parker")
example_child = Child(Id="peter", age=10, name_info=name_info_child)
name_info_parent = NameInfo(first_name="John", last_name="Johnathan")
example_parent = Parent(Id="John", name=name_info_parent, child=example_child)
name_info_other_parent = NameInfo(first_name="John", last_name="Martha")
other_parent = Parent(Id="Martha", name=name_info_other_parent, child=example_child)

other_name_info_child = NameInfo(first_name="alex", last_name="pupu")
other_child = Child(Id="alex", age=10, name_info=other_name_info_child)

data_model = DataModel.from_models(example_parent, other_parent, other_child)
print("unpatched:", [(reference_info.identifiable_id, reference_info.reference_id) for reference_info in data_model._reference_infos])
print("schemas:", [(schema.identifiable_id, schema.reference_id) for schema in data_model._schema_reference_infos])

patched_data_model = DataModelRebuilder(data_model).rebuild_data_model_for_AAS_structure()
print("patched:", [(reference_info.identifiable_id, reference_info.reference_id) for reference_info in data_model._reference_infos])


dict_store = BasyxFormatter().serialize(patched_data_model)

instance_graph = get_instance_graph(patched_data_model)
print(instance_graph)
type_graph = get_type_graph(patched_data_model)
print(type_graph)

visualize_graph(instance_graph, show=True)
visualize_graph(type_graph, show=True)
