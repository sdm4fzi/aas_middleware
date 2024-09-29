import json
from aas_middleware.model.formatting.aas.aas_model import (
    AAS,
    Submodel,
    SubmodelElementCollection,
)
from aas_middleware.model.formatting.aas import convert_aas_instance, convert_aas_template, convert_pydantic, convert_aas, convert_pydantic_model, convert_pydantic_type


def test_convert_simple_submodel(example_submodel: Submodel):
    basyx_aas_submodel = convert_pydantic.convert_model_to_submodel(example_submodel)
    pydantic_model = convert_aas.convert_submodel_to_model(basyx_aas_submodel)
    assert pydantic_model.model_dump_json() == example_submodel.model_dump_json()
    # TODO: fix bug with enums and literals...
    # assert pydantic_model.model_dump() == example_submodel.model_dump()

def test_convert_simple_submodel_template():
    basyx_aas_submodel_template = convert_pydantic_type.convert_model_to_submodel_template(Submodel)
    submodel_infered_type = convert_aas_template.convert_submodel_template_to_pydatic_type(basyx_aas_submodel_template)
    # TODO: implement assertion for correct type inference

def test_convert_simple_submodel_template(example_submodel: Submodel):
    basyx_aas_submodel = convert_pydantic_model.convert_model_to_submodel(example_submodel)
    basyx_aas_submodel_template = convert_pydantic_type.convert_model_instance_to_submodel_template(example_submodel)
    submodel_infered_type = convert_aas_template.convert_submodel_template_to_pydatic_type(basyx_aas_submodel_template)
    pydantic_model = convert_aas_instance.convert_submodel_to_model_instance(basyx_aas_submodel, submodel_infered_type)
    with open("tests/test_aas_middleware/model/formatting/aas/example_submodel.json", "w") as f:
        f.write(example_submodel.model_dump_json())
    with open("tests/test_aas_middleware/model/formatting/aas/recreated_submodel.json", "w") as f:
        f.write(pydantic_model.model_dump_json())
    # FIXME: resolve bug with wrong ordering of elements in submodel
    assert pydantic_model.model_dump_json() == example_submodel.model_dump_json()
    # # TODO: fix bug with enums and literals...
    # assert pydantic_model.model_dump() == example_submodel.model_dump()
    # assert json.dumps(pydantic_model.model_dump()) == json.dumps(example_submodel.model_dump())


def test_convert_simple_aas(example_aas: AAS):
    basyx_aas = convert_pydantic.convert_model_to_aas(example_aas)
    pydantic_models = convert_aas.convert_object_store_to_pydantic_models(basyx_aas)
    assert len(pydantic_models) == 1
    pydantic_model = pydantic_models[0]
    assert pydantic_model.model_dump_json() == example_aas.model_dump_json()
    # TODO: fix bug with enums and literals...
    # assert pydantic_model.model_dump() == example_aas.model_dump()