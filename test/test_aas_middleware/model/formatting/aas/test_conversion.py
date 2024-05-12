from aas_middleware.model.formatting.aas.aas_model import AAS, Submodel, SubmodelElementCollection
from aas_middleware.model.formatting.aas import convert_pydantic, convert_aas


def test_convert_simple_submodel(example_submodel: Submodel):
    basyx_aas_submodel = convert_pydantic.convert_pydantic_model_to_submodel(example_submodel)
    pydantic_model = convert_aas.convert_submodel_to_pydantic_model(basyx_aas_submodel)
    assert pydantic_model.model_dumb() == example_submodel.model_dump()

def test_convert_simple_aas(example_aas: AAS):
    basyx_aas = convert_pydantic.convert_pydantic_model_to_aas(example_aas)
    pydantic_models = convert_aas.convert_object_store_to_pydantic_models(basyx_aas)
    assert len(pydantic_models) == 1	
    pydantic_model = pydantic_models[0]
    assert pydantic_model.model_dumb() == example_aas.model_dump()

# def test_convert_special_submodel(example_special_sm_instance1: Submodel, example_special_sm_instance2: Submodel):
#     basyx_aas_submodel = convert_pydantic.convert_pydantic_model_to_submodel(example_special_sm_instance1)
#     pydantic_model = convert_aas.convert_submodel_to_pydantic_model(basyx_aas_submodel)
#     assert pydantic_model.dict() == example_special_sm_instance1.dict()
#     basyx_aas_submodel = convert_pydantic.convert_pydantic_model_to_submodel(example_special_sm_instance2)
#     pydantic_model = convert_aas.convert_submodel_to_pydantic_model(basyx_aas_submodel)
#     assert pydantic_model.dict() == example_special_sm_instance2.dict()

# def test_convert_special_aas(example_special_aas_instance: AAS):
#     basyx_aas = convert_pydantic.convert_pydantic_model_to_aas(example_special_aas_instance)
#     pydantic_models = convert_aas.convert_object_store_to_pydantic_models(basyx_aas)
#     assert len(pydantic_models) == 1	
#     pydantic_model = pydantic_models[0]
#     assert pydantic_model.dict() == example_special_aas_instance.model_dump()