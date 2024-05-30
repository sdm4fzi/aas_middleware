import base64
from urllib.parse import urlparse

from fastapi import HTTPException
from pydantic import BaseModel, ConfigDict

import basyx.aas.adapter.json
from basyx.aas import model
import json
from typing import Union, Any
import socket
import logging
logger = logging.getLogger(__name__)

class ClientModel(BaseModel):
    basyx_object: Union[model.AssetAdministrationShell, model.Submodel]

    model_config = ConfigDict(arbitrary_types_allowed=True)

    def to_dict(self) -> dict:
        basyx_json_string = json.dumps(
            self.basyx_object, cls=basyx.aas.adapter.json.AASToJsonEncoder
        )
        data: dict = json.loads(basyx_json_string)
                
        return data


def get_base64_from_string(string: str) -> str:
    b = base64.b64encode(bytes(string, "utf-8"))  # bytes
    base64_str = b.decode("utf-8")  # convert bytes to string
    return base64_str


def transform_client_to_basyx_model(
    client_model: dict | Any,
) -> Union[model.AssetAdministrationShell, model.Submodel]:
    """
    Function to transform a client model to a basyx model
    Args:
        response_model (dict): dictionary from server client that needs to be transformed
    Returns:
        Union[model.AssetAdministrationShell, model.Submodel]: basyx model from the given client model
    """
    if not isinstance(client_model, dict):
        client_model = client_model.to_dict()
    remove_empty_lists(client_model)
    json_model = json.dumps(client_model, indent=4)
    basyx_model = json.loads(json_model, cls=basyx.aas.adapter.json.AASFromJsonDecoder)
    return basyx_model

def remove_empty_lists(dictionary: dict) -> None:
    keys_to_remove = []
    for key, value in dictionary.items():
        if isinstance(value, dict):
            # Recursively process nested dictionaries
            remove_empty_lists(value)
            # if not value:
            #     keys_to_remove.append(key)
        elif isinstance(value, list) and value:
            # Recursively process nested lists
            for item in value:
                if isinstance(item, dict):
                    remove_empty_lists(item)
        elif isinstance(value, list) and not value:
            keys_to_remove.append(key)
    for key in keys_to_remove:
        del dictionary[key]


def is_server_online(adress: str):
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        parsed_url = urlparse(adress)
        host = parsed_url.hostname
        port = parsed_url.port
        sock.settimeout(2)  # 2 seconds
        sock.connect((host, port))
        sock.close()
        return True
    except (socket.timeout, ConnectionRefusedError):
        return False

async def check_sm_server_online(sm_server_adress: str):
    if not is_server_online(sm_server_adress):
        raise HTTPException(status_code=503, detail=f"Eror 503: Submodel Server cannot be reached at adress {sm_server_adress}")

async def check_aas_and_sm_server_online(aas_server_adress: str, submodel_server_adress: str):
    if not is_server_online(aas_server_adress):
        raise HTTPException(status_code=503, detail=f"Eror 503: AAS Server cannot be reached at adress {aas_server_adress}")
    if not is_server_online(submodel_server_adress):
        raise HTTPException(status_code=503, detail=f"Eror 503: Submodel Server cannot be reached at adress {submodel_server_adress}")
