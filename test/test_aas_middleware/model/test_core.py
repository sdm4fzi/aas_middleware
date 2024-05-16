from pydantic import BaseModel

from aas_middleware.model.core import Identifiable
from aas_middleware.model.formatting.aas.aas_model import BasyxModels
from aas_middleware.model.util import get_id


def test_get_id_of_aas_object(example_submodel_bom: BasyxModels):
    assert get_id(example_submodel_bom) == "object_id"
    Identifiable.model_validate(example_submodel_bom)
    submodel_as_dict = example_submodel_bom.model_dump()
    assert get_id(submodel_as_dict) == "object_id"
    Identifiable.model_validate(submodel_as_dict)

def test_get_id_of_basemodel(example_basemodel_bom_with_id: BaseModel):
    assert get_id(example_basemodel_bom_with_id) == "object_id"
    Identifiable.model_validate(example_basemodel_bom_with_id)
    base_model_as_dict = example_basemodel_bom_with_id.model_dump()
    assert get_id(base_model_as_dict) == "object_id"
    Identifiable.model_validate(base_model_as_dict)

def test_get_id_of_object(example_object_bom_with_id: object):
    assert get_id(example_object_bom_with_id) == "object_id"
    Identifiable.model_validate(example_object_bom_with_id)

def test_get_id_of_basemodel_with_identifier_attribute(example_basemodel_bom_with_identifier_attribute: BaseModel):
    assert get_id(example_basemodel_bom_with_identifier_attribute) == "object_id"
    Identifiable.model_validate(example_basemodel_bom_with_identifier_attribute)
    base_model_as_dict = example_basemodel_bom_with_identifier_attribute.model_dump()
    assert get_id(base_model_as_dict) == "id_named_attribute"
    Identifiable.model_validate(base_model_as_dict)

def test_get_id_of_object_with_identifier_attribute(example_object_with_identifier_attribute: object):
    assert get_id(example_object_with_identifier_attribute) == "object_id"
    Identifiable.model_validate(example_object_with_identifier_attribute)
