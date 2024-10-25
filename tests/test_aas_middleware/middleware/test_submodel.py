import asyncio
import json
import pytest

from fastapi.testclient import TestClient

from aas_middleware.middleware.middleware import Middleware


from tests.conftest import ExampleSubmodel, ValidAAS
from tests.test_aas_middleware.middleware.test_aas import get_clear_aas_and_submodel_server, post_aas, delete_aas


@pytest.mark.order(300)
def test_submodel_endpoint(client: TestClient, example_aas: ValidAAS):
    asyncio.run(get_clear_aas_and_submodel_server())

    post_aas(client, example_aas)
    
    get_submodel(client, example_aas)
    update_submodel(client, example_aas)
    delete_submodel(client, example_aas)
    post_submodel(client, example_aas)


def get_submodel(client: TestClient, example_aas_instance: ValidAAS):
    class_name = example_aas_instance.__class__.__name__
    example_submodel = example_aas_instance.example_submodel

    response = client.get(url=f"/{class_name}/{example_aas_instance.id}/example_submodel")
    assert response.status_code == 200
    assert response.text == example_submodel.model_dump_json()


def update_submodel(client: TestClient, example_aas_instance: ValidAAS):
    class_name = example_aas_instance.__class__.__name__
    example_submodel = example_aas_instance.example_submodel

    example_submodel.list_attribute = ["new_list_element"]

    data = example_submodel.model_dump_json()
    response = client.put(url=f"/{class_name}/{example_aas_instance.id}/example_submodel", content=data)

    assert response.status_code == 200
    updated_aas = client.get(url=f"/{class_name}/{example_aas_instance.id}/")
    assert updated_aas.status_code == 200
    assert updated_aas.json()["example_submodel"]["list_attribute"] == ["new_list_element"]

    updated_sm = client.get(url=f"/{class_name}/{example_aas_instance.id}/example_submodel")
    assert updated_sm.status_code == 200
    assert updated_sm.json()["list_attribute"] == ["new_list_element"]

    example_submodel.id = "new_id"
    example_submodel.id_short = "new_id"

    data = example_submodel.model_dump_json()
    response = client.put(url=f"/{class_name}/{example_aas_instance.id}/example_submodel", content=data)

    assert response.status_code == 200
    updated_aas = client.get(url=f"/{class_name}/{example_aas_instance.id}/")
    assert updated_aas.status_code == 200
    assert updated_aas.json()["example_submodel"]["id"] == "new_id"

    updated_sm = client.get(url=f"/{class_name}/{example_aas_instance.id}/example_submodel")
    assert updated_sm.status_code == 200
    assert updated_sm.json()["id"] == "new_id"


def delete_submodel(client: TestClient, example_aas_instance: ValidAAS):
    class_name = example_aas_instance.__class__.__name__

    response = client.delete(url=f"/{class_name}/{example_aas_instance.id}/example_submodel")
    assert response.status_code == 405 # example submodel cannot be deleted...

    response = client.delete(url=f"/{class_name}/{example_aas_instance.id}/optional_submodel")
    assert response.status_code == 200

    response = client.get(url=f"/{class_name}/{example_aas_instance.id}/optional_submodel")
    assert response.status_code == 200
    assert response.json() == None

    response = client.get(url=f"/{class_name}/{example_aas_instance.id}/")
    assert response.status_code == 200
    assert response.json()["optional_submodel"] == None


def post_submodel(client: TestClient, example_aas_instance: ValidAAS):
    class_name = example_aas_instance.__class__.__name__
    example_submodel = example_aas_instance.example_submodel

    data = example_submodel.model_dump_json()
    response = client.post(url=f"/{class_name}/{example_aas_instance.id}/example_submodel", content=data)
    assert response.status_code == 405 # example submodel cannot be posted...

    optional_submodel = example_aas_instance.optional_submodel
    optional_submodel.id = "new_posted_submodel_id"
    optional_submodel.id_short = "new_posted_submodel_id"

    data = optional_submodel.model_dump_json()
    response = client.post(url=f"/{class_name}/{example_aas_instance.id}/optional_submodel", content=data)
    assert response.status_code == 200

    response = client.get(url=f"/{class_name}/{example_aas_instance.id}/")
    assert response.status_code == 200
    assert response.json()["optional_submodel"]["id"] == "new_posted_submodel_id"

    response = client.get(url=f"/{class_name}/{example_aas_instance.id}/optional_submodel")
    assert response.status_code == 200
    assert response.text == optional_submodel.model_dump_json()
