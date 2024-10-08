from __future__ import annotations
import logging
from typing import List


from tests.conftest import TrivialFloatConnector

import aas_middleware

class ExampleSubmodel(aas_middleware.Submodel):
    float_attribute: float = 0.0
    rfid_tag_id: str
    position: tuple[int, int]


class ExampleAAS(aas_middleware.AAS):
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

data_model = aas_middleware.DataModel.from_models(example_aas)

middleware = aas_middleware.AasMiddleware()
middleware.load_aas_persistent_data_model(
    "test", data_model, "localhost", 8081, "localhost", 8081, persist_instances=True
)

trivial_float_connector = TrivialFloatConnector()
middleware.add_connector("test_connector", trivial_float_connector, model_type=float)

trivial_float_connector2 = TrivialFloatConnector()
middleware.add_connector(
    "test_persistence",
    trivial_float_connector2,
    model_type=float,
    data_model_name="test",
    model_id="example_aas_id",
    contained_model_id="example_submodel_id",
    field_id="float_attribute",
)


url = "opc.tcp://localhost:4840/freeopcua/server/"
namespace = "http://examples.freeopcua.github.io"
opc_ua_connector = aas_middleware.connectors.OpcUaConnector(url, namespace, "MyObject", "MyVariable")

middleware.add_connector(
    "opc_ua_connector",
    opc_ua_connector,
    model_type=float,
    data_model_name="test",
    model_id="example_aas_id",
    contained_model_id="example_submodel_id",
    field_id="float_attribute",
)

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



# The values for example b are injected by the middleware every time the workflow is called. However, to call it, a value for a and 
# example model has to be provided via the request body. 
@middleware.workflow(b=[1, 2, 3])
def example_workflow_with_arguments(a: str, b: List[int], example_model: ExampleAAS) -> ExampleSubmodel:
    logging.info("Example workflow")
    return example_model.example_submodel

if __name__ == "__main__":
    import uvicorn


    uvicorn.run("example_middleware:middleware.app", reload=True)
    # uvicorn.run(middleware.app)
