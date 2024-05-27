

import igraph as ig
from matplotlib import pyplot as plt
from pydantic import BaseModel
from aas_middleware.model.data_model import DataModel
from aas_middleware.model.reference_finder import ReferenceType
from aas_middleware.model.util import get_id_with_patch


def get_instance_graph(data_model: DataModel, name: str="Data Model Type Graph") -> ig.Graph:
    unique_names = set()
    for schema in data_model._reference_infos:
        unique_names.add(schema.identifiable_id)
        unique_names.add(schema.reference_id)
    n_vertices = len(unique_names)
    model_id_map = {model_id: counter for counter, model_id in enumerate(unique_names)}
    edges = [(model_id_map[reference_info.identifiable_id], model_id_map[reference_info.reference_id]) for reference_info in data_model._reference_infos]
    graph = ig.Graph(n_vertices, edges, directed=True)
    graph["title"] = name
    graph.vs["name"] = list(unique_names)
    node_types = []
    top_level_model_ids = set()
    for top_level_model_type in data_model.get_top_level_models().values():
        for model in top_level_model_type:
            top_level_model_ids.add(get_id_with_patch(model))
    for model_id in unique_names:
        if model_id in top_level_model_ids:
            node_types.append("Top Level")
        elif model_id in data_model.model_ids:
            node_types.append("Schema")
        else:
            node_types.append("Primitive")
    graph.vs["type"] = node_types
    graph.es["type"] = [reference_info.reference_type for reference_info in data_model._reference_infos]
    return graph


def get_type_graph(data_model: DataModel, name: str="Data Model Instance Graph") -> ig.Graph:
    unique_names = set()
    for schema in data_model._schema_reference_infos:
        unique_names.add(schema.identifiable_id)
        unique_names.add(schema.reference_id)
    n_vertices = len(unique_names)
    schema_id_map = {model_id: counter for counter, model_id in enumerate(unique_names)}
    edges = [(schema_id_map[reference_info.identifiable_id], schema_id_map[reference_info.reference_id]) for reference_info in data_model._schema_reference_infos]
    graph = ig.Graph(n_vertices, edges, directed=True)
    graph["title"] = name
    graph.vs["name"] = list(unique_names)
    node_types = []
    for type_name in unique_names:
        if type_name in data_model._top_level_schemas:
            node_types.append("Top Level")
        elif type_name in data_model._schemas:
            node_types.append("Schema")
        else:
            node_types.append("Primitive")
    graph.vs["type"] = node_types
    graph.es["type"] = [reference_info.reference_type for reference_info in data_model._schema_reference_infos]
    return graph

def visualize_graph(graph: ig.Graph):

    # graph.vs["name"] = ["\n\n" + label.split(".")[-1] for label in graph.vs["name"]]
    graph.vs["name"] = [label.split(".")[-1] for label in graph.vs["name"]]


    edge_colors = []
    for edge in graph.es["type"]:
        if edge == ReferenceType.ASSOCIATION:
            edge_colors.append("#0582ca")
        elif edge == ReferenceType.REFERENCE:
            edge_colors.append("#ade8f4")
        elif edge == ReferenceType.ATTRIBUTE:
            edge_colors.append("#ced4da")

    node_colors = []
    for node in graph.vs:
        if node["type"] == "Top Level":
            node_colors.append("#0582ca")
        elif node["type"] == "Schema":
            node_colors.append("#ade8f4")
        elif node["type"] == "Primitive":
            node_colors.append("#ced4da")

    fig, ax = plt.subplots()

    ig.plot(graph,
            target=ax,
            # layout="circle",
            vertex_color=node_colors,
            vertex_frame_width=0.0,
            vertex_size=30,
            vertex_label_size=7.0,
            vertex_label=graph.vs["name"],
            edge_width=2,
            edge_color=edge_colors,
    )
    fig.set_size_inches(10, 10)
    plt.show()
    # Save the graph as an image file
    # fig.savefig('social_network.png')
    # fig.savefig('social_network.jpg')
    # fig.savefig('social_network.pdf')


class GraphMetrics(BaseModel):
    number_of_vertices: int
    number_of_edges: int
    density: float
    diameter: int
    average_path_length: float

def calculate_graph_metrics(graph: ig.Graph) -> GraphMetrics:
    return GraphMetrics(
        number_of_vertices=graph.vcount(),
        number_of_edges=graph.ecount(),
        density=graph.density(),
        diameter=graph.diameter(),
        average_path_length=graph.average_path_length()
    )