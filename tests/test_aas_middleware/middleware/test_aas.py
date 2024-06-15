import pytest

from fastapi.testclient import TestClient

from aas_middleware.middleware.middleware import Middleware


from tests.conftest import ValidAAS

@pytest.mark.order(200)
def test_aas_endpoint(client: TestClient, example_aas: ValidAAS):
    assert_empty_aas(client, example_aas)
    post_aas(client, example_aas)
    changed_aas = example_aas.model_copy(deep=True)
    changed_aas.id = "new_id"
    post_aas(client, changed_aas)
    
    get_aas(client, example_aas)
    get_aas(client, changed_aas)

    get_all_aas(client, example_aas)

    update_aas(client, example_aas)
    delete_aas(client, example_aas)
    delete_aas(client, changed_aas)
    assert_empty_aas(client, example_aas)

def post_aas(client: TestClient, example_aas: ValidAAS):
    data = example_aas.model_dump_json()
    class_name = example_aas.__class__.__name__
    response = client.post(url=f"/{class_name}/", content=data)
    assert response.status_code == 200 
    response = client.post(url=f"/{class_name}/", content=data)
    assert response.status_code == 400

def get_aas(client: TestClient, example_aas: ValidAAS):
    # FIXME: this endpoint is not working properly...
    class_name = example_aas.__class__.__name__
    response = client.get(url=f"/{class_name}/{example_aas.id}/")
    assert response.status_code == 200
    assert response.json() == example_aas.model_dump_json()

def get_all_aas(client: TestClient, example_aas: ValidAAS):
    class_name = example_aas.__class__.__name__
    response = client.get(url=f"/{class_name}/")
    assert response.status_code == 200
    json_content = response.json()
    aas_ids = set([aas["id"] for aas in json_content])
    assert aas_ids == {example_aas.id, "new_id"}

def assert_empty_aas(client: TestClient, example_aas: ValidAAS):
    class_name = example_aas.__class__.__name__
    response = client.get(url=f"/{class_name}/")
    assert response.status_code == 200
    assert response.json() == []

def update_aas(client: TestClient, example_aas: ValidAAS):
    class_name = example_aas.__class__.__name__
    example_aas.id_short = "new_id_short"
    example_aas.example_submodel.list_attribute = ["new_list_element"]
    response = client.put(url=f"/{class_name}/{example_aas.id}/", content=example_aas.model_dump_json())
    assert response.status_code == 200

    updated_aas = client.get(url=f"/{class_name}/{example_aas.id}/")
    assert updated_aas.json()["id_short"] == "new_id_short"
    assert updated_aas.json()["example_submodel"]["list_attribute"] == ["new_list_element"]
    
    example_aas.example_submodel.id = "new_id"
    response = client.put(url=f"/{class_name}/{example_aas.id}/", content=example_aas.model_dump_json())
    assert response.status_code == 400

def delete_aas(client: TestClient, example_aas: ValidAAS):
    class_name = example_aas.__class__.__name__
    response = client.delete(url=f"/{class_name}/{example_aas.id}/")
    assert response.status_code == 200
    response = client.get(url=f"/{class_name}/{example_aas.id}/")
    assert response.status_code == 400

