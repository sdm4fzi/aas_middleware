import logging
import os
import time
from typing import Set
import pytest

from fastapi.testclient import TestClient

import asyncio
import aiohttp


from tests.conftest import AAS_SERVER_ADDRESS, AAS_SERVER_PORT, SUBMODEL_SERVER_ADDRESS, SUBMODEL_SERVER_PORT, ValidAAS

async def get_clear_aas_and_submodel_server():
    aas_response = None
    submodel_response = None
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(f"http://{AAS_SERVER_ADDRESS}:{AAS_SERVER_PORT}/shells") as response_aas:
                if response_aas.status == 200: 
                    aas_response = await response_aas.json()
            async with session.get(f"http://{SUBMODEL_SERVER_ADDRESS}:{SUBMODEL_SERVER_PORT}/submodels") as response_sm:
                if response_sm.status == 200:
                    submodel_response = await response_sm.json()
    except Exception:
        pass
    
    if not aas_response or not submodel_response:
        logging.info("Could not connect to the docker container. Starting a new one.")
        result = os.system("docker-compose -f docker/docker-compose-dev.yaml up -d")
        if result != 0:
            raise Exception("Could not start the docker container.")
    elif aas_response["result"] != [] or submodel_response["result"] != []:
        logging.info("Docker container is not empty. Restarting it.")
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
                            logging.info("AAS Docker containers are running.")
                            break
        except Exception:
            pass
        if time.time() - start > 40:
            raise Exception("Timeout: Could not connect to the docker container.")
        await asyncio.sleep(1)



@pytest.mark.order(200)
def test_aas_endpoint(client: TestClient, example_aas: ValidAAS):
    """
    Test the complete AAS endpoint functionality including:
    - Creating AAS instances
    - Retrieving AAS instances
    - Updating AAS instances
    - Deleting AAS instances
    - Listing all AAS instances
    """
    # Verify initial state - no AAS instances should exist
    all_ids = get_all_aas(client, example_aas)
    assert all_ids == set(), "Expected no AAS instances initially"
    
    # Test creating and retrieving the first AAS
    post_aas(client, example_aas)
    get_aas(client, example_aas)

    # Test creating a second AAS with different id/id_short
    changed_aas = example_aas.model_copy(deep=True)
    # Note: When only id_short is provided, id is automatically set to the same value
    changed_aas.id_short = "new_id"
    changed_aas.id = "new_id"
    post_aas(client, changed_aas)
    get_aas(client, changed_aas)

    # Verify both AAS instances exist
    all_ids = get_all_aas(client, example_aas)
    assert all_ids == {example_aas.id, changed_aas.id}, f"Expected both AAS instances, got {all_ids}"

    # Test updating the first AAS
    update_aas(client, example_aas)
    all_ids = get_all_aas(client, example_aas)
    assert all_ids == {example_aas.id, changed_aas.id}, "AAS instances should still exist after update"

    # Test deleting both AAS instances
    delete_aas(client, example_aas)
    delete_aas(client, changed_aas)

    # Verify final state - no AAS instances should exist
    all_ids = get_all_aas(client, example_aas)
    assert all_ids == set(), "Expected no AAS instances after deletion"

def post_aas(client: TestClient, example_aas: ValidAAS):
    """Test creating an AAS instance and verify duplicate creation fails."""
    data = example_aas.model_dump_json()
    class_name = example_aas.__class__.__name__
    
    # First POST should succeed
    response = client.post(url=f"/{class_name}/", content=data)
    assert response.status_code == 200, f"Failed to create AAS: {response.status_code} - {response.text}"
    
    # Second POST with same data should fail (duplicate)
    response = client.post(url=f"/{class_name}/", content=data)
    assert response.status_code == 400, f"Expected duplicate creation to fail, got {response.status_code} - {response.text}"

def get_aas(client: TestClient, example_aas: ValidAAS):
    """Test retrieving an AAS instance and verify the response matches expected data."""
    class_name = example_aas.__class__.__name__
    response = client.get(url=f"/{class_name}/{example_aas.id}")
    
    if response.status_code != 200:
        print(f"Error: {response.status_code} - {response.text}")
    assert response.status_code == 200, f"Failed to retrieve AAS: {response.status_code} - {response.text}"
    
    # Compare the response with the expected AAS
    # Note: We compare JSON strings to handle enum serialization differences
    # For now, compare the JSON strings to avoid enum serialization issues
    # TODO: Implement proper enum comparison if needed
    assert response.text == example_aas.model_dump_json(), "Retrieved AAS data does not match expected data"

def get_all_aas(client: TestClient, example_aas: ValidAAS) -> Set[str]:
    """Test retrieving all AAS instances and return their IDs."""
    class_name = example_aas.__class__.__name__
    response = client.get(url=f"/{class_name}/")
    assert response.status_code == 200, f"Failed to retrieve all AAS instances: {response.status_code} - {response.text}"
    
    json_content = response.json()
    aas_ids = set([aas["id"] for aas in json_content])
    return aas_ids

def update_aas(client: TestClient, example_aas: ValidAAS):
    """Test updating an AAS instance and verify the changes are persisted."""
    class_name = example_aas.__class__.__name__
    old_example_aas_id = example_aas.id

    # Update AAS fields
    example_aas.id_short = "new_changed_id"
    example_aas.id = "new_changed_id"
    example_aas.example_submodel.list_attribute = ["new_list_element"]

    # Update the AAS
    response = client.put(url=f"/{class_name}/{old_example_aas_id}/", content=example_aas.model_dump_json())
    assert response.status_code == 200, f"Failed to update AAS: {response.status_code} - {response.text}"

    # Verify the update
    updated_aas = client.get(url=f"/{class_name}/{example_aas.id}/")
    assert updated_aas.status_code == 200, f"Failed to retrieve updated AAS: {updated_aas.status_code} - {updated_aas.text}"
    assert updated_aas.json()["id_short"] == "new_changed_id", "AAS id_short was not updated correctly"
    assert updated_aas.json()["example_submodel"]["list_attribute"] == ["new_list_element"], "Submodel list_attribute was not updated correctly"
    
    # Update submodel fields
    example_aas.example_submodel.id = "new_changed_submodel_id"
    example_aas.example_submodel.id_short = "new_changed_submodel_id"
    response = client.put(url=f"/{class_name}/{example_aas.id}/", content=example_aas.model_dump_json())

    assert response.status_code == 200, f"Failed to update AAS submodel: {response.status_code} - {response.text}"
    updated_aas = client.get(url=f"/{class_name}/{example_aas.id}/")
    assert updated_aas.status_code == 200, f"Failed to retrieve AAS after submodel update: {updated_aas.status_code} - {updated_aas.text}"
    assert updated_aas.json()["example_submodel"]["id"] == "new_changed_submodel_id", "Submodel id was not updated correctly"


def delete_aas(client: TestClient, example_aas: ValidAAS):
    """Test deleting an AAS instance and verify it no longer exists."""
    class_name = example_aas.__class__.__name__
    response = client.delete(url=f"/{class_name}/{example_aas.id}/")
    assert response.status_code == 200, f"Failed to delete AAS: {response.status_code} - {response.text}"
    
    # Verify the AAS no longer exists
    response = client.get(url=f"/{class_name}/{example_aas.id}/")
    assert response.status_code == 400, f"Expected AAS to be deleted, but it still exists: {response.status_code} - {response.text}"

