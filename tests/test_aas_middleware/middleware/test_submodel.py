import json
import pytest

from fastapi.testclient import TestClient

from aas_middleware.middleware.middleware import Middleware


from tests.conftest import ValidAAS
from tests.test_aas_middleware.middleware.test_aas import post_aas, delete_aas, assert_empty_aas


@pytest.mark.order(300)
def test_submodel_endpoint(client: TestClient, example_aas: ValidAAS):
    assert_empty_aas(client, example_aas)
    post_aas(client, example_aas)
    
    # post_submodel(client, example_aas)
    get_submodel(client, example_aas)
    update_submodel(client, example_aas)
    # delete_submodel(client, example_aas)

    delete_aas(client, example_aas)
    assert_empty_aas(client, example_aas)

def post_submodel(client: TestClient, example_aas_instance: ValidAAS):
    # TODO: only do this on an optional attribute that is empty before
    class_name = example_aas_instance.__class__.__name__
    example_submodel = example_aas_instance.example_submodel
    example_submodel.id = "PMP2"
    data = example_submodel.model_dump_json()
    sm_class_name = example_submodel.__class__.__name__
    response = client.post(url=f"/{class_name}/{example_aas_instance.id}/{sm_class_name}", content=data)
    assert response.status_code == 200
    response = client.post(url=f"/{class_name}/{example_aas_instance.id}/{sm_class_name}", content=data)
    assert response.status_code == 413
    # response = client.get(url=f"/{class_name}/{example_aas_instance.id}/")
    # assert response.status_code == 200
    # assert response.json()["process_model"] == example_submodel.model_dump_json()


def get_submodel(client: TestClient, example_aas_instance: ValidAAS):
    class_name = example_aas_instance.__class__.__name__
    example_submodel = example_aas_instance.example_submodel
    sm_class_name = example_submodel.__class__.__name__

    response = client.get(url=f"/{class_name}/{example_aas_instance.id}/{sm_class_name}")
    assert response.status_code == 200
    assert response.json() == example_submodel.model_dump()

def update_submodel(client: TestClient, example_aas_instance: ValidAAS):
    class_name = example_aas_instance.__class__.__name__
    example_submodel = example_aas_instance.example_submodel
    sm_class_name = example_submodel.__class__.__name__
    example_submodel.list_attribute = ["new_list_element"]
    data = example_submodel.model_dump_json()
    response = client.put(url=f"/{class_name}/{example_aas_instance.id}/{sm_class_name}", content=data)
    assert response.status_code == 200
    updated_aas = client.get(url=f"/{class_name}/{example_aas_instance.id}/")
    assert updated_aas.json()["example_submodel_id"]["list_attribute"] == ["new_list_element"]
    example_submodel.id = "new_id"
    response = client.put(url=f"/{class_name}/{example_aas_instance.id}/ProcessModel", content=data)
    assert response.status_code == 200

def delete_submodel(client: TestClient, example_aas_instance: ValidAAS):
    # TODO: only do this on an optional attribute that is empty before
    class_name = example_aas_instance.__class__.__name__
    sm_class_name = example_aas_instance.example_submodel.__class__.__name__
    response = client.delete(url=f"/{class_name}/{example_aas_instance.id}/{sm_class_name}")
    assert response.status_code == 200
    response = client.get(url=f"/{class_name}/{example_aas_instance.id}/{sm_class_name}")
    assert response.status_code == 411
    response = client.get(url=f"/{class_name}/{example_aas_instance.id}/")
    assert response.status_code == 200
    assert response.json()["process_model"] == None