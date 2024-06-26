from __future__ import annotations
import logging

from aas_middleware.connect.connectors.opc_ua_client_connector import OpcUaConnector
from aas_middleware.model.formatting.aas import aas_model
from tests.conftest import TrivialFloatConnector

from aas_middleware.model.data_model import DataModel
from aas_middleware.middleware.aas_persistence_middleware import AasMiddleware


class ExampleSubmodel(aas_model.Submodel):
    float_attribute: float = 0.0
    rfid_tag_id: str
    position: tuple[int, int]


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
        rfid_tag_id="1234",
        position=(1, 0),
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


class ExampleSensorConnector:
    # This class is a placeholder for a real connector to a sensor with opc ua, mqtt or so...
    def __init__(self, rfid_id: str):
        self.rfid_id = rfid_id

    async def provide(self) -> str:
        return self.rfid_id
    
example_rfid_connector_1 = ExampleSensorConnector("1234")
example_rfid_connector_2 = ExampleSensorConnector("5678")

resource_positions = {
    example_rfid_connector_1: (0, 0),
    example_rfid_connector_2: (1, 1),
}
    
@middleware.workflow(interval=10)
async def read_rfid():
    logging.info("Reading RFID")
    for connector, position in resource_positions.items():
        rfid_id = await connector.provide()
        if rfid_id is None:
            continue
        if not rfid_id == "1234":
            logging.info(f"RFID {rfid_id} not found in resource_positions")
            continue
        model_persistence = middleware.persistence_registry.get_connector_by_data_model_and_model_id("test", "example_aas_id")
        model: ExampleAAS = await model_persistence.provide()
        model.example_submodel.position = position
        await model_persistence.consume(model)
        logging.info(f"Updated position of resource with RFID {rfid_id} to {position}")


if __name__ == "__main__":
    import uvicorn

    uvicorn.run("example_middleware:middleware.app", reload=True)
