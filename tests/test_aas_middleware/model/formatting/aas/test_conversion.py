from aas_middleware.model.formatting.aas.aas_model import (
    AAS,
    Submodel,
    SubmodelElementCollection,
)
from aas_middleware.model.formatting.aas import convert_pydantic, convert_aas


def test_convert_simple_submodel(example_submodel: Submodel):
    basyx_aas_submodel = convert_pydantic.convert_model_to_submodel(example_submodel)
    pydantic_model = convert_aas.convert_submodel_to_model(basyx_aas_submodel)
    print(pydantic_model.model_dump())
    print(example_submodel.model_dump())
    assert pydantic_model.model_dump_json() == example_submodel.model_dump_json()
    # TODO: fix bug with enums and literals...
    # assert pydantic_model.model_dump() == example_submodel.model_dump()


def test_convert_simple_aas(example_aas: AAS):
    basyx_aas = convert_pydantic.convert_model_to_aas(example_aas)
    pydantic_models = convert_aas.convert_object_store_to_pydantic_models(basyx_aas)
    assert len(pydantic_models) == 1
    pydantic_model = pydantic_models[0]
    assert pydantic_model.model_dump_json() == example_aas.model_dump_json()
    # TODO: fix bug with enums and literals...
    # assert pydantic_model.model_dump() == example_aas.model_dump()