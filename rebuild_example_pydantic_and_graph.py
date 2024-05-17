from __future__ import annotations
from typing import List, Optional

from pydantic import BaseModel, create_model

from aas_middleware.model.data_model import DataModel
from aas_middleware.model.data_model_rebuilder import DataModelRebuilder, get_patched_aas_object
from aas_middleware.model.formatting.aas import aas_model
from aas_middleware.model.formatting.aas.aas_formatter import AASFormatter
from aas_middleware.model.reference_finder import ReferenceType

class Child(BaseModel):
    Id: str
    age: int

class NameInfo(BaseModel):
    # TODO: rework bug with creating ids here and not updating the values in the data model correctly...
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
name_info_other_parent = NameInfo(first_name="Martha", last_name="Martha")
other_parent = Parent(Id="Martha", name=name_info_other_parent, child=example_child)

other_name_info_child = NameInfo(first_name="alex", last_name="pupu")
other_child = Child(Id="alex", age=10, name_info=other_name_info_child)

data_model = DataModel.from_models(example_parent, other_parent, other_child)

patched_data_model = DataModelRebuilder(data_model).rebuild_data_model_for_AAS_structure()

dict_store = AASFormatter().serialize(patched_data_model)
print(len(dict_store))
for value in dict_store:
    print(value, value.id_short)


model_id_map = {model_id: counter for counter, model_id in enumerate(data_model.model_ids)}

import igraph as ig
from matplotlib import pyplot as plt

print(data_model.model_ids)
# TODO: solve problem of self referencing reference_info...
print([(reference_info.identifiable_id, reference_info.reference_id) for reference_info in data_model._reference_infos])

n_vertices = len(data_model.model_ids)
edges = [(model_id_map[reference_info.identifiable_id], model_id_map[reference_info.reference_id]) for reference_info in data_model._reference_infos]
g = ig.Graph(n_vertices, edges)

# Set attributes for the graph, nodes, and edges
g["title"] = "Data Model"
g.vs["name"] = list(data_model.model_ids)
g.es["type"] = [reference_info.reference_type for reference_info in data_model._reference_infos]

# Plot in matplotlib
# Note that attributes can be set globally (e.g. vertex_size), or set individually using arrays (e.g. vertex_color)
fig, ax = plt.subplots(figsize=(5,5))
ig.plot(
    g,
    target=ax,
    layout="circle", # print nodes in a circular layout
    vertex_size=30,
    vertex_frame_width=4.0,
    vertex_frame_color="white",
    vertex_label=g.vs["name"],
    vertex_label_size=7.0,
    edge_width=[2 if reference_type == ReferenceType.ASSOCIATION else 1 for reference_type in g.es["type"]],
    edge_color=["#7142cf" if reference_type == ReferenceType.ASSOCIATION else "#AAA" for reference_type in g.es["type"]]
)

plt.show()

# # Save the graph as an image file
# fig.savefig('social_network.png')
# fig.savefig('social_network.jpg')
# fig.savefig('social_network.pdf')
print(g.indegree())
print(g.shell_index())