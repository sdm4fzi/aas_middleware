from typing import Dict, Literal, Optional
import igraph as ig
from matplotlib import pyplot as plt
from pydantic import BaseModel
from aas_middleware.model.data_model import DataModel
from aas_middleware.model.reference_finder import ReferenceType
from aas_middleware.model.util import get_id_with_patch


def get_instance_graph(
    data_model: DataModel, name: str = "Data Model Type Graph"
) -> ig.Graph:
    unique_names = set()
    for schema in data_model._reference_infos:
        unique_names.add(schema.identifiable_id)
        unique_names.add(schema.reference_id)
    n_vertices = len(unique_names)
    model_id_map = {model_id: counter for counter, model_id in enumerate(unique_names)}
    edges = [
        (
            model_id_map[reference_info.identifiable_id],
            model_id_map[reference_info.reference_id],
        )
        for reference_info in data_model._reference_infos
    ]
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
    graph.es["type"] = [
        reference_info.reference_type for reference_info in data_model._reference_infos
    ]
    return graph


def get_type_graph(
    data_model: DataModel, name: str = "Data Model Instance Graph"
) -> ig.Graph:
    unique_names = set()
    for schema in data_model._schema_reference_infos:
        unique_names.add(schema.identifiable_id)
        unique_names.add(schema.reference_id)
    n_vertices = len(unique_names)
    schema_id_map = {model_id: counter for counter, model_id in enumerate(unique_names)}
    edges = [
        (
            schema_id_map[reference_info.identifiable_id],
            schema_id_map[reference_info.reference_id],
        )
        for reference_info in data_model._schema_reference_infos
    ]
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
    graph.es["type"] = [
        reference_info.reference_type
        for reference_info in data_model._schema_reference_infos
    ]
    return graph


def visualize_graph(graph: ig.Graph, show: bool = False, save: Optional[Literal["png", "jpg", "svg"]] = None):

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
    node_labels = []
    for node in graph.vs:
        if node["type"] == "Top Level":
            node_colors.append("#0582ca")
            node_labels.append(node["name"])
        elif node["type"] == "Schema":
            node_colors.append("#ade8f4")
            node_labels.append(node["name"])
        elif node["type"] == "Primitive":
            node_colors.append("#ced4da")
            # node_labels.append("")
            node_labels.append(node["name"])

    fig, ax = plt.subplots()

    # _layout_mapping = {
    #     "auto": "layout_auto",
    #     "automatic": "layout_auto",
    #     "bipartite": "layout_bipartite",
    #     "circle": "layout_circle",
    #     "circular": "layout_circle",
    #     "davidson_harel": "layout_davidson_harel",
    #     "dh": "layout_davidson_harel",
    #     "drl": "layout_drl",
    #     "fr": "layout_fruchterman_reingold",
    #     "fruchterman_reingold": "layout_fruchterman_reingold",
    #     "graphopt": "layout_graphopt",
    #     "grid": "layout_grid",
    #     "kk": "layout_kamada_kawai",
    #     "kamada_kawai": "layout_kamada_kawai",
    #     "lgl": "layout_lgl",
    #     "large": "layout_lgl",
    #     "large_graph": "layout_lgl",
    #     "mds": "layout_mds",
    #     "random": "layout_random",
    #     "rt": "layout_reingold_tilford",
    #     "tree": "layout_reingold_tilford",
    #     "reingold_tilford": "layout_reingold_tilford",
    #     "rt_circular": "layout_reingold_tilford_circular",
    #     "reingold_tilford_circular": "layout_reingold_tilford_circular",
    #     "sphere": "layout_sphere",
    #     "spherical": "layout_sphere",
    #     "star": "layout_star",
    #     "sugiyama": "layout_sugiyama",
    # }

    ig.plot(
        graph,
        target=ax,
        # layout="circle",
        layout="kk",
        vertex_color=node_colors,
        vertex_frame_width=0.0,
        vertex_size=10,
        vertex_label_size=7.0,
        vertex_label=node_labels,
        edge_width=1,
        edge_color=edge_colors,
    )
    fig.set_size_inches(20, 20)
    if show:
        plt.show()
    # plt.show()
    # Save the graph as an image file
    if save == "png":
        fig.savefig(f"{graph["title"]}.png")
    elif save == "jpg":
        fig.savefig(f"{graph["title"]}.jpg")
    elif save == "svg":
        fig.savefig(f"{graph["title"]}.svg")

import numpy as np


class GraphMetrics(BaseModel):
    name: str
    number_of_vertices: int
    number_of_edges: int
    density: float
    in_degree_mean: float
    in_degree_std: float
    out_degree_mean: float
    out_degree_std: float


def calculate_graph_metrics(graph: ig.Graph) -> GraphMetrics:
    indegree = np.array(graph.indegree())
    outdegree = np.array(graph.outdegree())

    return GraphMetrics(
        name=graph["title"],
        number_of_vertices=graph.vcount(),
        number_of_edges=graph.ecount(),
        density=graph.density(),
        in_degree_mean=np.mean(indegree),
        in_degree_std=np.std(indegree),
        out_degree_mean=np.mean(outdegree),
        out_degree_std=np.std(outdegree),
    )
