import json
import typing
from fastapi import HTTPException
from pydantic import BaseModel
import uvicorn
import aas_middleware
from aas_middleware.middleware.model_registry_api import register_model_from_middleware
from aas_middleware.middleware.sync.synced_connector import SyncDirection, SyncRole
from aas_middleware.model.formatting.aas.basyx_formatter import BasyxTemplateFormatter

middleware = aas_middleware.Middleware()


## mockup classes to work without ontology or mqtt connection^

class ExampleTransferUnit(BaseModel):
    # this model would be generated dynamically from ontology, only mockup here
    id: str
    conveyor_speed: float
    mqtt_broker_ip: str
    mqtt_broker_port: int


class MockupMqttConnector:
    def __init__(self, host: str, port: int):
        self.return_value = 0.0  # Default return value

    async def connect(self):
        pass

    async def disconnect(self):
        pass

    async def consume(self, body: float) -> None:
        print(body)
        self.return_value = body  # Update the return value with the consumed body
        pass

    async def provide(self) -> float:
        return self.return_value


async def get_ontology_data_json_schema() -> dict:
    # This function would normally fetch the ontology data, map it to json schema and return it.
    # Here we return a mockup json schema for the ExampleTransferUnit.
    return ExampleTransferUnit.model_json_schema()

async def load_ontology_instance_data() -> ExampleTransferUnit:
    return ExampleTransferUnit(
        id="ExampleTransferUnit",
        conveyor_speed=-1,
        mqtt_broker_ip="hivemq.example.com",
        mqtt_broker_port=1883,
    )

@middleware.workflow()
async def load_ontology_data_model() -> dict[str, str]:
    # 1. get the type of the ontology data at first
    ontology_data_type = await get_ontology_data_json_schema()
    # 2. register the ontology data type in the middleware
    register_model_from_middleware(
        model_name="ExampleTransferUnit",
        model=ontology_data_type,
        middleware_instance=middleware,
    )
    return {
        "result": "Ontology data model registered successfully",
    }


@middleware.workflow()
async def load_ontology_instance_data_and_register_connector() -> dict[str, str]:
    # 2. load the ontology data
    ontology_instance = await load_ontology_instance_data()
    # 3. persist the ontology instance data
    await middleware.persist(
        data_model_name="ExampleTransferUnit",
        model=ontology_instance,
    )

    # 4. create mqtt connector
    mqtt_connector = MockupMqttConnector(
        host=ontology_instance.mqtt_broker_ip,
        port=ontology_instance.mqtt_broker_port,
    )
    # 5. register the connector in the middleware and sync it with the data model
    middleware.add_synced_connector(
        connector_id="mqtt_connector",
        connector=mqtt_connector,
        model_type=float,  # Assuming the connector provides a float value
        data_model_name="ExampleTransferUnit",
        model_id=ontology_instance.id,
        field_id="conveyor_speed",
        sync_role=SyncRole.GROUND_TRUTH,
        sync_direction=SyncDirection.TO_PERSISTENCE
    )
    # 6. force FastAPI to rebuild its OpenAPI schema so `/docs` sees it:
    middleware.app.openapi_schema = None
    return {
        "result": "Ontology data and connector registered successfully",
    }


# 7. To test everything, use the connector with the rest API, consume some example values and check if the data instance changed.

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(middleware.app)


""" Use the following curls to test:

1. Create the data model with
    curl -X 'POST' \
    'http://127.0.0.1:8000/workflows/load_ontology_data_model/execute' \
    -H 'accept: application/json' \
    -d '' 

2. refresh the docs page, the DataModel `ExampleTransferUnit` should be visible in the `/docs` page. You can query the model with:
    curl -X 'GET' \
    'http://127.0.0.1:8000/ExampleTransferUnit/' \
    -H 'accept: application/json'

-> you should see an empty list since no data instance is created yet.
3. Create the data instance and register the connector with:
    curl -X 'POST' \
        'http://127.0.0.1:8000/workflows/load_ontology_instance_data_and_register_connector/execute' \
        -H 'accept: application/json' \
        -d ''

4. Query now the data again with the command from the second step, you should see the following output:
    [
        {
            "id": "ExampleTransferUnit",
            "conveyor_speed": 0.0,
            "mqtt_broker_ip": "hivemq.example.com",
            "mqtt_broker_port": 1883
        }
    ]

5. If you reload the /docs page, you should see the connector `mqtt_connector` in the `/connectors/` section.

6. Now you can use the connector to consume some values, e.g. setting the conveyor speed to 1.2 with:
    curl -X 'POST' \
    'http://127.0.0.1:8000/connectors/mqtt_connector/value?value=1.2' \
    -H 'accept: application/json' \
    -d ''

7. Query the data again with the command from the second step, you should see the following output:
    [
        {
            "id": "ExampleTransferUnit",
            "conveyor_speed": 1.2,
            "mqtt_broker_ip": "hivemq.example.com",
            "mqtt_broker_port": 1883
        }
    ]

We see that upon arrival of a mqtt message (here manually created with the curl command), the data instance is updated and saved in the persistence.

What to do next:
- Create a real MQTT connector with  "receive" function (this function is automatically synced) for async communication or use the existing MQTT connector from the aas-middleware from the connectors folder
- Create a Formatter that allows to convert ontologies to json schema and apply it instead of the mockup function `get_ontology_data_json_schema`
- Create a real ontology instance data loading function that fetches the data from the ontology and applies it instead of the mockup function `load_ontology_instance_data`
- Test if everything works as expected with the real ontology and MQTT connector.
"""
