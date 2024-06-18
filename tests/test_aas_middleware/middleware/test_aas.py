import os
import time
from typing import Set
import pytest

from fastapi.testclient import TestClient

import asyncio
import aiohttp
from aas_middleware.middleware.middleware import Middleware


from tests.conftest import AAS_SERVER_ADDRESS, AAS_SERVER_PORT, SUBMODEL_SERVER_ADDRESS, SUBMODEL_SERVER_PORT, ValidAAS

async def get_clear_aas_and_submodel_server():
    aas_response = None
    submodel_response = None
    async with aiohttp.ClientSession() as session:
        async with session.get(f"http://{AAS_SERVER_ADDRESS}:{AAS_SERVER_PORT}/shells") as response_aas:
            if response_aas.status == 200: 
                aas_response = await response_aas.json()
        async with session.get(f"http://{SUBMODEL_SERVER_ADDRESS}:{SUBMODEL_SERVER_PORT}/submodels") as response_sm:
            if response_sm.status == 200:
                submodel_response = await response_sm.json()
    
    if not aas_response or not submodel_response:
        result = os.system("docker-compose -f docker/docker-compose-dev.yaml up -d")
        if result != 0:
            raise Exception("Could not start the docker container.")
    elif aas_response["result"] != [] or submodel_response["result"] != []:
        result = os.system("docker-compose -f docker/docker-compose-dev.yaml restart")
        if result != 0:
            raise Exception("Could not restart the docker container.")
    else:
        return
    await asyncio.sleep(1)
    start = time.time()
    while True:
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(f"http://{AAS_SERVER_ADDRESS}:{AAS_SERVER_PORT}/shells") as response_aas:
                    async with session.get(f"http://{SUBMODEL_SERVER_ADDRESS}:{SUBMODEL_SERVER_PORT}/submodels") as response_sm:
                        if response_aas.status == 200 and response_sm.status == 200:
                            break
        except:
            pass
        if time.time() - start > 20:
            raise Exception("Timeout: Could not connect to the docker container.")
        await asyncio.sleep(1)



@pytest.mark.order(200)
def test_aas_endpoint(client: TestClient, example_aas: ValidAAS):
    asyncio.run(get_clear_aas_and_submodel_server())
    all_ids = get_all_aas(client, example_aas)
    assert all_ids == set()
    post_aas(client, example_aas)
    get_aas(client, example_aas)

    changed_aas = example_aas.model_copy(deep=True)

    # FIXME: fix bug that id and id_short need to be the same...
    changed_aas.id = "new_id"
    changed_aas.id_short = "new_id"
    post_aas(client, changed_aas)
    get_aas(client, changed_aas)

    all_ids = get_all_aas(client, example_aas)
    assert all_ids == {example_aas.id, changed_aas.id}

    update_aas(client, example_aas)
    all_ids = get_all_aas(client, example_aas)
    assert all_ids == {example_aas.id, changed_aas.id}

    delete_aas(client, example_aas)
    delete_aas(client, changed_aas)

    all_ids = get_all_aas(client, example_aas)
    assert all_ids == set()

def post_aas(client: TestClient, example_aas: ValidAAS):
    data = example_aas.model_dump_json()
    class_name = example_aas.__class__.__name__
    response = client.post(url=f"/{class_name}/", content=data)
    assert response.status_code == 200 
    response = client.post(url=f"/{class_name}/", content=data)
    assert response.status_code == 400

def get_aas(client: TestClient, example_aas: ValidAAS):
    class_name = example_aas.__class__.__name__
    response = client.get(url=f"/{class_name}/{example_aas.id}/")
    assert response.status_code == 200
    # FIXME: fix bug with enum values
    # assert response.json() == example_aas.model_dump()
    assert response.text == example_aas.model_dump_json()

def get_all_aas(client: TestClient, example_aas: ValidAAS) -> Set[str]:
    class_name = example_aas.__class__.__name__
    response = client.get(url=f"/{class_name}/")
    assert response.status_code == 200
    json_content = response.json()
    aas_ids = set([aas["id"] for aas in json_content])
    return aas_ids

def update_aas(client: TestClient, example_aas: ValidAAS):
    class_name = example_aas.__class__.__name__

    old_example_aas_id = example_aas.id

    example_aas.id_short = "new_changed_id"
    example_aas.id = "new_changed_id"
    example_aas.example_submodel.list_attribute = ["new_list_element"]

    response = client.put(url=f"/{class_name}/{old_example_aas_id}/", content=example_aas.model_dump_json())
    assert response.status_code == 200

    updated_aas = client.get(url=f"/{class_name}/{example_aas.id}/")
    assert updated_aas.json()["id_short"] == "new_changed_id"
    assert updated_aas.json()["example_submodel"]["list_attribute"] == ["new_list_element"]
    
    example_aas.example_submodel.id = "new_changed_submodel_id"
    example_aas.example_submodel.id_short = "new_changed_submodel_id"
    response = client.put(url=f"/{class_name}/{example_aas.id}/", content=example_aas.model_dump_json())

    assert response.status_code == 200
    updated_aas = client.get(url=f"/{class_name}/{example_aas.id}/")
    assert updated_aas.json()["example_submodel"]["id"] == "new_changed_submodel_id"


def delete_aas(client: TestClient, example_aas: ValidAAS):
    class_name = example_aas.__class__.__name__
    response = client.delete(url=f"/{class_name}/{example_aas.id}/")
    assert response.status_code == 200
    response = client.get(url=f"/{class_name}/{example_aas.id}/")
    assert response.status_code == 400

