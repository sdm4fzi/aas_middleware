import queue

from matplotlib import pyplot as plt

import aas_middleware
from aas_middleware.model.data_model_visualizer import calculate_graph_metrics, get_type_graph, visualize_graph


from data_models.sdm_reference_model.product import Product
from data_models.sdm_reference_model.resources import Resource
from data_models.sdm_reference_model.procedure import Procedure
from data_models.sdm_reference_model.processes import Process
from data_models.sdm_reference_model.order import Order
from data_models.sdm_reference_model.performance import Performance
from data_models.sdm_reference_model.change_scenario import ChangeScenario

data_model = aas_middleware.DataModel.from_model_types(Product, Resource, Procedure, Process, Order, Performance, ChangeScenario)
# instance_graph = get_instance_graph(patched_data_model)
type_graph = get_type_graph(data_model, "SDM Reference Model")
print(calculate_graph_metrics(type_graph).model_dump_json())

# visualize_graph(instance_graph)
# visualize_graph(type_graph, save="svg")

from data_models.morpheus.morpheus_model import (
    ProcessData,
    WorkStation,
    ProductionLine,
    PoleHousing,
    Order,
    GameRound,
    Training,
    WorkProcess,
    EditablePart,
    EditableVariant
)

# morpheus_data_model = DataModel.from_model_types(ProcessData, WorkStation, ProductionLine, PoleHousing, Order, GameRound, Training, WorkProcess, EditablePart, EditableVariant)
# morpheus_data_model.patch_schema_references()
# # instance_graph = get_instance_graph(patched_data_model)
# morpheus_type_graph = get_type_graph(morpheus_data_model, "Morpheus")
# print(calculate_graph_metrics(morpheus_type_graph))

# # visualize_graph(instance_graph)
# visualize_graph(morpheus_type_graph)

from data_models.flexisv1.flexisv1 import FLEXIS_TYPES_LIST


flexis_data_model = aas_middleware.DataModel.from_model_types(*FLEXIS_TYPES_LIST)
# instance_graph = get_instance_graph(patched_data_model)
flexis_type_graph = get_type_graph(flexis_data_model, "Flexis")
print(calculate_graph_metrics(flexis_type_graph).model_dump_json())

# visualize_graph(instance_graph)
# visualize_graph(flexis_type_graph, save="svg")



# from prodsys.models import (
#     node_data,
#     product_data,
#     resource_data,
#     processes_data,
#     time_model_data,
#     state_data,
#     performance_data,
#     performance_indicators,
#     scenario_data,
#     queue_data,
#     sink_data,
#     source_data,
# )

# import prodsys


# prodsys_data_model = DataModel.from_model_types(
#     prodsys.adapters.ProductionSystemAdapter
# )
# prodsys_data_model.patch_schema_references()

# # instance_graph = get_instance_graph(patched_data_model)
# prodsys_type_graph = get_type_graph(prodsys_data_model, "prodsys")
# print(calculate_graph_metrics(prodsys_type_graph))


# # visualize_graph(instance_graph)
# visualize_graph(prodsys_type_graph)


# from data_models.simplan.simplan_model import Model


# simplan_data_model = DataModel.from_model_types(Model)
# # instance_graph = get_instance_graph(patched_data_model)
# simplan_type_graph = get_type_graph(simplan_data_model, "simplan")

# print(calculate_graph_metrics(simplan_type_graph))

# # visualize_graph(instance_graph)
# visualize_graph(simplan_type_graph, save="svg")

plt.show()
