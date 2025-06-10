import json
import typing
from fastapi import HTTPException
import uvicorn
import aas_middleware
from aas_middleware.middleware.model_registry_api import register_model_from_middleware
from aas_middleware.model.formatting.aas.basyx_formatter import BasyxTemplateFormatter

middleware = aas_middleware.Middleware()

middleware.generate_model_registry_api()


TRANFER_UNIT_JSON_SCHEMA = {
    "$defs": {
        "ConveyorBelt": {
            "properties": {
                "id": {
                    "anyOf": [
                        {"type": "string"},
                        {"type": "integer"},
                        {"format": "uuid", "type": "string"},
                    ],
                    "title": "Id",
                },
                "ConveyorSpeed": {"$ref": "#/$defs/ConveyorSpeed"},
                "parent_id": {
                    "default": "https://www.sfb1574.kit.edu/ontologies/TransferUnit#TransferUnit",
                    "title": "Parent Id",
                    "type": "string",
                },
                "id_short": {
                    "default": "ConveyorBelt",
                    "title": "Id Short",
                    "type": "string",
                },
                "semantic_id": {
                    "default": "https://www.sfb1574.kit.edu/ontologies/TransferUnit#ConveyorBelt",
                    "title": "Semantic Id",
                    "type": "string",
                },
            },
            "required": ["id", "ConveyorSpeed"],
            "title": "ConveyorBelt",
            "type": "object",
        },
        "ConveyorSpeed": {
            "properties": {
                "id": {
                    "default": "https://www.sfb1574.kit.edu/ontologies/inf#InterfaceAccessibleMQTTParameter",
                    "title": "Id",
                    "type": "string",
                },
                "value": {
                    "anyOf": [{"type": "number"}, {"type": "null"}],
                    "default": None,
                    "title": "Value",
                },
                "id_short": {
                    "default": "ConveyorSpeed",
                    "title": "Id Short",
                    "type": "string",
                },
                "MQTTTopic": {
                    "semantic_id": "https://www.sfb1574.kit.edu/ontologies/inf#hasMQTTTopic",
                    "title": "Mqtttopic",
                    "type": "string",
                },
                "MQTTBrokerIP": {
                    "semantic_id": "https://www.sfb1574.kit.edu/ontologies/inf#hasMQTTBrokerIP",
                    "title": "Mqttbrokerip",
                    "type": "string",
                },
                "semantic_id": {
                    "default": "https://www.sfb1574.kit.edu/ontologies/TransferUnit#hasConveyorSpeed",
                    "title": "Semantic Id",
                    "type": "string",
                },
                "parameter_type": {
                    "default": "MQTTParameter",
                    "title": "Parameter Type",
                    "type": "string",
                },
            },
            "required": ["MQTTTopic", "MQTTBrokerIP"],
            "title": "ConveyorSpeed",
            "type": "object",
        },
        "LightBarrier": {
            "properties": {
                "id": {
                    "anyOf": [
                        {"type": "string"},
                        {"type": "integer"},
                        {"format": "uuid", "type": "string"},
                    ],
                    "title": "Id",
                },
                "Occupied": {"$ref": "#/$defs/Occupied"},
                "parent_id": {
                    "default": "https://www.sfb1574.kit.edu/ontologies/TransferUnit#TransferUnit",
                    "title": "Parent Id",
                    "type": "string",
                },
                "id_short": {
                    "default": "LightBarrier",
                    "title": "Id Short",
                    "type": "string",
                },
                "semantic_id": {
                    "default": "https://www.sfb1574.kit.edu/ontologies/TransferUnit#LightBarrier",
                    "title": "Semantic Id",
                    "type": "string",
                },
            },
            "required": ["id", "Occupied"],
            "title": "LightBarrier",
            "type": "object",
        },
        "Occupied": {
            "properties": {
                "id": {
                    "default": "https://www.sfb1574.kit.edu/ontologies/inf#InterfaceAccessibleMQTTParameter",
                    "title": "Id",
                    "type": "string",
                },
                "value": {
                    "anyOf": [{"type": "boolean"}, {"type": "null"}],
                    "default": None,
                    "title": "Value",
                },
                "id_short": {
                    "default": "Occupied",
                    "title": "Id Short",
                    "type": "string",
                },
                "MQTTTopic": {
                    "semantic_id": "https://www.sfb1574.kit.edu/ontologies/inf#hasMQTTTopic",
                    "title": "Mqtttopic",
                    "type": "string",
                },
                "MQTTBrokerIP": {
                    "semantic_id": "https://www.sfb1574.kit.edu/ontologies/inf#hasMQTTBrokerIP",
                    "title": "Mqttbrokerip",
                    "type": "string",
                },
                "semantic_id": {
                    "default": "https://www.sfb1574.kit.edu/ontologies/TransferUnit#isOccupied",
                    "title": "Semantic Id",
                    "type": "string",
                },
                "parameter_type": {
                    "default": "MQTTParameter",
                    "title": "Parameter Type",
                    "type": "string",
                },
            },
            "required": ["MQTTTopic", "MQTTBrokerIP"],
            "title": "Occupied",
            "type": "object",
        },
    },
    "properties": {
        "id": {
            "anyOf": [
                {"type": "string"},
                {"type": "integer"},
                {"format": "uuid", "type": "string"},
            ],
            "title": "Id",
        },
        "ConveyorBelts": {
            "default": [],
            "items": {"$ref": "#/$defs/ConveyorBelt"},
            "title": "Conveyorbelts",
            "type": "array",
        },
        "LightBarriers": {
            "default": [],
            "items": {"$ref": "#/$defs/LightBarrier"},
            "title": "Lightbarriers",
            "type": "array",
        },
        "id_short": {"default": "TransferUnit", "title": "Id Short", "type": "string"},
        "semantic_id": {
            "default": "https://www.sfb1574.kit.edu/ontologies/TransferUnit#TransferUnit",
            "title": "Semantic Id",
            "type": "string",
        },
    },
    "required": ["id"],
    "title": "TransferUnit",
    "type": "object",
}

# either use /register_model endpoint or programmatically register the model with this:
# register_model_from_middleware(
#     model_name="TransferUnit",
#     model=TRANFER_UNIT_JSON_SCHEMA,
#     middleware_instance=middleware,
# )

if __name__ == "__main__":
    # uvicorn.run("minimal_example:middleware.app", reload=True)
    uvicorn.run(middleware.app)
