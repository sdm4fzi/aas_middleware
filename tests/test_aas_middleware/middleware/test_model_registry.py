# import pytest

# import json


# @pytest.mark.order(100)
# def test_register_model(client, loaded_middleware, example_aas_instance):
#     # 1. make example_aas_instance to dict annd remove the id
#     dict_aas = example_aas_instance.dict()
#     del dict_aas["id"]
#     json_aas = json.dumps(dict_aas)
#     # 2. register the model in the middleware
#     response = client.post(url="/register_model?model_name=example_model", content=json_aas)
#     assert response.status_code == 403
#     # 4. make example_aas_instance to dict, where the bill of material is missing the id
#     dict_aas = example_aas_instance.dict()  
#     del dict_aas["bill_of_material"]["id"]
#     json_aas = json.dumps(dict_aas)
#     response = client.post(url="/register_model/?model_name=example_model", content=json_aas)
#     assert response.status_code == 403
#     # 2. check, if the response code is 200
#     json_aas = example_aas_instance.json()
#     response = client.post(url="/register_model/?model_name=example_model", content=json_aas)
#     assert response.status_code == 200
#     # 3. check, if the model is in the middleware loaded as model
#     assert any("example_model" == model.__name__ for model in loaded_middleware.models)
#     # 4. check that the model is in the routers and the open api schema of the app
#     assert any("example_model" in router.path for router in loaded_middleware.app.routes)
#     assert any("example_model" in loaded_middleware.app.openapi_schema["components"]["schemas"] for router in loaded_middleware.app.routes)
#     # 5. test that resending the same model returns a 403
#     response = client.post(url="/register_model/?model_name=example_model", content=json_aas)
#     assert response.status_code == 403
#     # 6. test the get_models endpoint (200, model in the response)
#     response = client.get(url="/get_models")
#     assert response.status_code == 200
#     # TODO: fix this assertion, this is not working completely yet
#     # print(response.json())
#     # print(example_aas_instance.schema())
#     # assert response.json() == [example_aas_instance.schema()]

#     # 7. test the update model endpoint (200, model updated in the middleware, routers and openapi schema, 403, 404)
#     # remove bill of materials from model
#     dict_aas = example_aas_instance.dict()
#     del dict_aas["bill_of_material"]
#     response = client.put(url="/update_model?model_name=example_model", content=json_aas)
#     assert response.status_code == 200
#     response = client.put(url="/update_model?model_name=non_existing_name", content=json_aas)
#     assert response.status_code == 403
#     # 7. test the delete model endpoint (200, model deleted in the middleware, routers and openapi schema, 403, 404)
#     response = client.delete(url="/delete_model?model_name=example_model")
#     assert response.status_code == 200
#     assert not any("example_model" == model.__name__ for model in loaded_middleware.models)
#     assert not any("example_model" in router.path for router in loaded_middleware.app.routes)
#     assert not any("example_model" in loaded_middleware.app.openapi_schema["components"]["schemas"] for router in loaded_middleware.app.routes)
#     response = client.delete(url="/delete_model?model_name=non_existing_name")
#     assert response.status_code == 404
