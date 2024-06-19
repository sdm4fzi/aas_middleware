# def test_starting_aas_middleware(example_aas: ProductAas):
# TODO: make this test work so that it does not stop after running the uvicorn.run() function


from __future__ import annotations

from aas_middleware.connect.connectors.opc_ua_client_connector import OpcUaConnector
from aas_middleware.model.formatting.aas import aas_model
from tests.conftest import TrivialFloatConnector

from aas_middleware.model.data_model import DataModel
from aas_middleware.middleware.aas_persistence_middleware import AasMiddleware


class ExampleSubmodel(aas_model.Submodel):
    float_attribute: float = 0.0


class ExampleAAS(aas_model.AAS):
    example_submodel: ExampleSubmodel


example_aas = ExampleAAS(
    id="example_aas_id",
    id_short="example_aas_id",
    description="Example AAS",
    example_submodel=ExampleSubmodel(
        id="example_submodel_id",
        id_short="example_submodel_id",
        description="Example Submodel",
        float_attribute=0.0,
    ),
)

data_model = DataModel.from_models(example_aas)

middleware = AasMiddleware()
middleware.load_aas_persistent_data_model(
    "test", data_model, "localhost", 8081, "localhost", 8081, initial_loading=True
)

trivial_float_connector = TrivialFloatConnector()
middleware.add_connector("test_connector", trivial_float_connector, model_type=float)
middleware.add_connector(
    "test_persistence",
    trivial_float_connector,
    model_type=float,
    data_model_name="test",
    model_id="example_aas_id",
    contained_model_id="example_submodel_id",
    field_id="float_attribute",
)


url = "opc.tcp://localhost:4840/freeopcua/server/"
namespace = "http://examples.freeopcua.github.io"
opc_ua_connector = OpcUaConnector(url, namespace, "MyObject", "MyVariable")

middleware.add_connector(
    "opc_ua_connector",
    opc_ua_connector,
    model_type=float,
    data_model_name="test",
    model_id="example_aas_id",
    contained_model_id="example_submodel_id",
    field_id="float_attribute",
)

middleware.generate_connector_endpoints()

if __name__ == "__main__":
    import uvicorn

    uvicorn.run("check_running_middleware:middleware.app", reload=True)
    print(143)
