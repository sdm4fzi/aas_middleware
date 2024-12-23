import copy
from typing import Any, Dict, Optional

from aas_pydantic.aas_model import (
    AAS,
    Submodel,
)
from aas_pydantic import (
    convert_aas_instance,
    convert_aas_template,
    convert_pydantic_model,
    convert_pydantic_type,
)
from aas_middleware.model.formatting.util import compare_schemas


def test_convert_simple_submodel(example_submodel: Submodel):
    # TODO: tuple and list SEC attributes make problems here...tuples are lists and list SECs contain strange element with no values?
    basyx_aas_submodel = convert_pydantic_model.convert_model_to_submodel(
        example_submodel
    )
    pydantic_model = convert_aas_instance.convert_submodel_to_model_instance(
        basyx_aas_submodel
    )
    for key in pydantic_model.model_dump():
        if not key in example_submodel.model_dump():
            print("missing key", key)
        if not pydantic_model.model_dump()[key] == example_submodel.model_dump()[key]:
            print("different values")
            print(pydantic_model.model_dump()[key])
            print(example_submodel.model_dump()[key])
    assert pydantic_model.model_dump() == example_submodel.model_dump()


def test_convert_simple_submodel_template():
    basyx_aas_submodel_template = (
        convert_pydantic_type.convert_model_to_submodel_template(Submodel)
    )
    submodel_infered_type = (
        convert_aas_template.convert_submodel_template_to_pydatic_type(
            basyx_aas_submodel_template
        )
    )
    assert compare_schemas(
        Submodel.model_json_schema(), submodel_infered_type.model_json_schema()
    )


def test_convert_simple_submodel_with_template_extraction(example_submodel: Submodel):
    basyx_aas_submodel = convert_pydantic_model.convert_model_to_submodel(
        example_submodel
    )
    basyx_aas_submodel_template = (
        convert_pydantic_type.convert_model_instance_to_submodel_template(
            example_submodel
        )
    )

    submodel_infered_type = (
        convert_aas_template.convert_submodel_template_to_pydatic_type(
            basyx_aas_submodel_template
        )
    )
    assert compare_schemas(
        example_submodel.model_json_schema(), submodel_infered_type.model_json_schema()
    )

    pydantic_model = convert_aas_instance.convert_submodel_to_model_instance(
        basyx_aas_submodel, submodel_infered_type
    )
    assert pydantic_model.model_dump() == example_submodel.model_dump()


def test_convert_simple_aas(example_aas: AAS):
    #     # TODO: update this to new type / instance conversion
    object_store = convert_pydantic_type.convert_model_to_aas_template(
        type(example_aas)
    )
    pydantic_type = convert_aas_template.convert_object_store_to_pydantic_types(
        object_store
    )
    assert len(pydantic_type) == 1
    # FIXME: this test sometimes fails due to a failure when handling union and optional types with the same submodel linked (optional_submodel and union_submodel)
    # resolve this problem by making the concept descriptions more precise for individual submodels while still only use one submodel reference for one type.
    assert compare_schemas(
        example_aas.model_json_schema(), pydantic_type[0].model_json_schema()
    )

    object_store_instance = convert_pydantic_model.convert_model_to_aas(example_aas)
    pydantic_instance = convert_aas_instance.convert_object_store_to_pydantic_models(
        object_store_instance, types=pydantic_type
    )
    assert len(pydantic_instance) == 1
    assert pydantic_instance[0].model_dump() == example_aas.model_dump()
