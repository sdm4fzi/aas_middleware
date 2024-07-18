import asyncio
import logging

from fastapi.testclient import TestClient
from httpx import Response



from aas_middleware.connect.workflows.worfklow_description import WorkflowDescription
from tests.conftest import ValidAAS, ExampleSubmodel
from tests.test_aas_middleware.middleware.test_aas import get_all_aas, get_clear_aas_and_submodel_server, post_aas



def execute_workflow(client: TestClient, workflow_name: str) -> Response:
    response = client.post(url=f"/workflows/{workflow_name}/execute/")
    return response


def execute_workflow_background(client: TestClient, workflow_name: str) -> Response:
    response = client.post(url=f"/workflows/{workflow_name}/execute_background/")
    return response


def interrupt_workflow(client: TestClient, workflow_name: str) -> Response:
    response = client.get(url=f"/workflows/{workflow_name}/interrupt/")
    return response

def get_workflow_description(client: TestClient, workflow_name: str) -> Response:
    response = client.get(url=f"/workflows/{workflow_name}/description/")
    return response


def test_example_workflow(client: TestClient):
    response = execute_workflow(client, "example_workflow")
    assert response.status_code == 200
    assert response.json() == True

    response = get_workflow_description(client, "example_workflow")
    assert response.status_code == 200

    assert response.text == WorkflowDescription(
        name="example_workflow",
        running=False,
        on_startup=False,
        on_shutdown=False,
        interval=None,
        providers=[],
        consumers=[],

    ).model_dump_json()

    response = execute_workflow_background(client, "example_workflow")
    assert response.status_code == 200
    assert response.json() == {"message": f"Started exeuction of workflow example_workflow"}

    response = get_workflow_description(client, "example_workflow")
    assert response.status_code == 200

    assert response.text == WorkflowDescription(
        name="example_workflow",
        running=False,
        on_startup=False,
        on_shutdown=False,
        interval=None,
        providers=[],
        consumers=[],

    ).model_dump_json()



# def test_example_workflow_interval(client: TestClient):
#    # FIXME: resolve problem that the execution in the background is not possible during testing, by hand it is working...
#     logging.info("test_example_workflow_interval")
#     response = execute_workflow_background(client, "example_workflow_interval")
#     logging.info("started workflow execution in background")
#     logging.info(response.json())
#     assert response.status_code == 200
#     assert response.json() == {'message': 'Started exeuction of workflow example_workflow_interval'}

#     response = get_workflow_description(client, "example_workflow_interval")
#     assert response.status_code == 200

#     assert response.text == WorkflowDescription(
#         name="example_workflow_interval",
#         running=True,
#         on_startup=False,
#         on_shutdown=False,
#         interval=1.0,
#         providers=[],
#         consumers=[],

#     ).model_dump_json()

    ## TODO: 
    # 1. test executing running twice -> failure
    # 2. test interruption
    # 3. test running in background and interrupting
    

    # response = execute_workflow_background(client, "example_workflow_interval")
    # assert response.status_code == 404
    # # assert response.status_code == 200
    # # assert response.json() == {"message": f"Started exeuction of workflow example_workflow_interval"}

    # response = get_workflow_description(client, "example_workflow_interval")
    # assert response.status_code == 200

    # assert response.text == WorkflowDescription(
    #     name="example_workflow_interval",
    #     running=False,
    #     on_startup=False,
    #     on_shutdown=False,
    #     interval=1.0,
    #     providers=[],
    #     consumers=[],
    # ).model_dump_json()

    # # stop workflow
    # response = interrupt_workflow(client, "example_workflow_interval")
    # assert response.status_code == 200


    # response = get_workflow_description(client, "example_workflow_interval")
    # assert response.status_code == 200
    # assert response.text == WorkflowDescription(
    #     name="example_workflow_interval",
    #     running=False,
    #     on_startup=False,
    #     on_shutdown=False,
    #     interval=1.0,
    #     providers=[],
    #     consumers=[],
    # ).model_dump_json()