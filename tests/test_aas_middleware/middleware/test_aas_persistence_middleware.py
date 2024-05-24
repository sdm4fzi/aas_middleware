from __future__ import annotations

from tests.conftest import (
    ProductAas,
)

from aas_middleware.model.data_model import DataModel
from aas_middleware.middleware.aas_persistence_middleware import AasMiddleware

def test_loading_data_model_into_aas_middleware(example_aas: ProductAas):

    data_model = DataModel.from_models(example_aas)

    middleware  = AasMiddleware()
    middleware.load_aas_persistent_data_model("test", data_model, "localhost", 8081, "localhost", 8081)


# def test_starting_aas_middleware(example_aas: ProductAas):
        # TODO: make this test work so that it does not stop after running the uvicorn.run() function

#     data_model = DataModel.from_models(example_aas)

#     middleware  = AasMiddleware()
#     middleware.load_aas_persistent_data_model("test", data_model, "localhost", 8081, "localhost", 8081)

#     import uvicorn

#     uvicorn.run(middleware.app)
#     print(143)