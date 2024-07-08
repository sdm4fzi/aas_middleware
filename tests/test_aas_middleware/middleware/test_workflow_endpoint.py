# import pytest

# from fastapi.testclient import TestClient



# from tests.conftest import ValidAAS, ExampleSubmodel




# @pytest.mark.order(200)
# def test_connector_endpoint(client: TestClient, example_submodel: ExampleSubmodel):
#     response = client.get(url=f"/connectors/test_connector/")
#     assert response.status_code == 200
#     assert response.json() == 1.0

#     response = client.post(url=f"/connectors/test_connector/", content=2.0)
#     assert response.status_code == 200


# def get_example_aas_from_server(client: TestClient, example_aas: ExampleSubmodel):
#     class_name = example_aas.__class__.__name__
#     example_aas_from_server_response = client.get(url=f"/{class_name}/{example_aas.id}/")
#     example_aas_from_server = ValidAAS.model_validate(example_aas_from_server_response.json())
#     return example_aas_from_server


# @pytest.mark.order(200)
# def test_connected_connector_endpoint(client: TestClient, example_aas: ExampleSubmodel):
#     response = client.get(url=f"/connectors/test_connected_connector/")
#     assert response.status_code == 200
#     example_aas_from_server = get_example_aas_from_server(client, example_aas)
#     assert response.json() == example_aas_from_server.example_submodel.float_attribute

#     response = client.post(url=f"/connectors/test_connected_connector/", content=2.0)
#     assert response.status_code == 200

#     example_aas_from_server = get_example_aas_from_server(client, example_aas)
#     assert example_aas_from_server.example_submodel.float_attribute == 2.0

#     response = client.get(url=f"/connectors/test_connected_connector/")
#     assert response.status_code == 200
#     example_aas_from_server = get_example_aas_from_server(client, example_aas)
#     assert response.json() == example_aas_from_server.example_submodel.float_attribute
#     assert response.json() == 1.0