from __future__ import annotations

import time
import pytest
from fastapi.testclient import TestClient

from aas_middleware.middleware.middleware import Middleware
from tests.conftest import (
    AAS_SERVER_ADDRESS,
    AAS_SERVER_PORT,
    SUBMODEL_SERVER_ADDRESS,
    SUBMODEL_SERVER_PORT,
    ValidAAS,
)

import uvicorn
import threading

from aas_middleware.model.data_model import DataModel
from aas_middleware.middleware.aas_persistence_middleware import AasMiddleware


def test_loading_data_model_into_aas_middleware(example_aas: ValidAAS):

    data_model = DataModel.from_models(example_aas)

    middleware = AasMiddleware()
    middleware.load_aas_persistent_data_model(
        "test",
        data_model,
        AAS_SERVER_ADDRESS,
        AAS_SERVER_PORT,
        SUBMODEL_SERVER_ADDRESS,
        SUBMODEL_SERVER_PORT,
    )

@pytest.mark.order(100)
def test_starting_aas_middleware(example_aas: ValidAAS):
    data_model = DataModel.from_models(example_aas)

    middleware = AasMiddleware()
    middleware.load_aas_persistent_data_model(
        "test",
        data_model,
        AAS_SERVER_ADDRESS,
        AAS_SERVER_PORT,
        SUBMODEL_SERVER_ADDRESS,
        SUBMODEL_SERVER_PORT,
    )
    with TestClient(middleware.app) as test_client:
        response = test_client.get(url="/openapi.json")
        assert response.status_code == 200
        # with open("openapi.json", "w") as f:
        #     f.write(response.text)