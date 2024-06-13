# def test_starting_aas_middleware(example_aas: ProductAas):
# TODO: make this test work so that it does not stop after running the uvicorn.run() function


from __future__ import annotations

from tests.conftest import (
    ValidAAS,
    ExampleSubmodel,
    ExampleSubmodel2,
    ExampleSEC,
)

from aas_middleware.model.data_model import DataModel
from aas_middleware.middleware.aas_persistence_middleware import AasMiddleware

example_aas = ValidAAS(
    id_short="product_aas",
    example_submodel_2=ExampleSubmodel2(
        id_short="bom", components=["comp1", "comp2"], num_components=2
    ),
    info=ExampleSubmodel(
        id_short="product_info",
        product_name="product1",
        manufacturer="manufacturer1",
        product_version=ExampleSEC(
            id_short="version_info", version="1.2.2", product_type="type1"
        ),
    ),
)

data_model = DataModel.from_models(example_aas)

middleware = AasMiddleware()
middleware.load_aas_persistent_data_model(
    "test", data_model, "localhost", 8081, "localhost", 8081
)


# example body:
"""
{
    "id_short": "string",
    "description": "",
    "id": "string",
    "example_submodel": {
        "id_short": "string3",
        "description": "",
        "id": "string3",
        "semantic_id": "",
        "components": ["string"],
        "num_components": 0,
    },
    "info": {
        "id_short": "string1",
        "description": "",
        "id": "string1",
        "semantic_id": "",
        "product_name": "string",
        "manufacturer": "string",
        "product_version": {
            "id_short": "string2",
            "description": "",
            "semantic_id": "",
            "version": "string",
            "product_type": "string",
        },
    },
}
"""
if __name__ == "__main__":
    import uvicorn

    uvicorn.run("check_running_middleware:middleware.app", reload=True)
    print(143)
