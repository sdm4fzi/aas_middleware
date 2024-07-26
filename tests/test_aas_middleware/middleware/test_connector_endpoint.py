import asyncio

from fastapi.testclient import TestClient



from aas_middleware.middleware.connector_router import ConnectorDescription
from aas_middleware.middleware.registries import ConnectionInfo
from tests.conftest import ValidAAS, ExampleSubmodel
from tests.test_aas_middleware.middleware.test_aas import get_all_aas, get_clear_aas_and_submodel_server, post_aas




def test_connector_endpoint(client: TestClient, example_submodel: ExampleSubmodel):
    response = client.get(url=f"/connectors/test_connector/description/")
    assert response.status_code == 200
    assert response.text == ConnectorDescription(
        connector_id="test_connector",
        connector_type="TrivialFloatConnector",
        persistence_connection=None,
        model_type="float",
    ).model_dump_json()

    response = client.get(url=f"/connectors/test_connector/value/")
    assert response.status_code == 200
    assert response.json() == 1.0

    response = client.post(url=f"/connectors/test_connector/value/", params={"value": 2.0})
    assert response.status_code == 200


def get_example_aas_from_server(client: TestClient, example_aas: ExampleSubmodel):
    class_name = example_aas.__class__.__name__
    example_aas_from_server_response = client.get(url=f"/{class_name}/{example_aas.id}/")
    example_aas_from_server = ValidAAS.model_validate(example_aas_from_server_response.json())
    return example_aas_from_server


def test_connected_connector_endpoint(client: TestClient, example_aas: ExampleSubmodel):
    asyncio.run(get_clear_aas_and_submodel_server())

    response = client.get(url="/connectors/test_connected_connector/description/")
    assert response.status_code == 200
    assert response.text == ConnectorDescription(
        connector_id="test_connected_connector",
        connector_type="TrivialFloatConnector",
        persistence_connection=ConnectionInfo(
            data_model_name="test",
            model_id="valid_aas_id",
            contained_model_id="example_submodel_id",
            field_id="float_attribute",
        ),
        model_type="float",
    ).model_dump_json()
    all_ids = get_all_aas(client, example_aas)
    assert all_ids == set()
    post_aas(client, example_aas)
    response = client.get(url=f"/connectors/test_connected_connector/value")
    assert response.status_code == 200
    example_aas_from_server = get_example_aas_from_server(client, example_aas)
    assert response.json() == example_aas_from_server.example_submodel.float_attribute

    response = client.post(url=f"/connectors/test_connected_connector/value", params={"value": 2.0})
    assert response.status_code == 200

    example_aas_from_server = get_example_aas_from_server(client, example_aas)
    assert example_aas_from_server.example_submodel.float_attribute == 2.0

    response = client.get(url=f"/connectors/test_connected_connector/value")
    assert response.status_code == 200
    example_aas_from_server = get_example_aas_from_server(client, example_aas)
    assert response.json() == example_aas_from_server.example_submodel.float_attribute
    assert response.json() == 1.0