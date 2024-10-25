from pydantic import BaseModel
from aas_middleware.model.data_model import DataModel

from aas_middleware.model.util import get_id_with_patch, normalize_identifiables, normalize_identifiables_in_model
from tests.conftest import (
    ExampleSubmodel,
    ValidAAS,
    ExampleSubmodel2,
    ExampleSubmodelWithReference,
    ObjectBomWithId,
    ExampleBaseMdelWithId,
    BaseModelWithIdentifierAttribute,
    ObjectWithIdentifierAttribute,
    ExampleSubmodelWithIdReference,
    ExampleBasemodelWithAssociation,
)


def test_minimal_example_with_AAS(example_aas: ValidAAS):
    data_model = DataModel.from_models(example_aas)
    assert data_model.get_model("valid_aas_id") == example_aas
    assert data_model.get_model("example_submodel_id") == example_aas.example_submodel
    assert len(data_model._key_ids_models) == 8 # 1 aas, 4 submodels, 3 submodel element collections
    assert data_model.get_models_of_type_name("ValidAAS") == [example_aas]
    assert data_model.get_models_of_type(ValidAAS) == [example_aas]
    example_submodel_models = data_model.get_models_of_type_name("ExampleSubmodel")
    example_submodel_ids = set([get_id_with_patch(model) for model in example_submodel_models])
    assert example_submodel_ids == {"example_submodel_id", "example_submodel_for_union_id", "example_optional_submodel_id"}
    example_submodel_models = data_model.get_models_of_type(ExampleSubmodel)
    example_submodel_ids = set([get_id_with_patch(model) for model in example_submodel_models])
    assert example_submodel_ids == {"example_submodel_id", "example_submodel_for_union_id", "example_optional_submodel_id"}
    assert data_model.get_referencing_models(example_aas.example_submodel) == [example_aas]
    submodel_references = data_model.get_referenced_models(example_aas.example_submodel)
    submodel_references_id_set = set([get_id_with_patch(reference) for reference in submodel_references])
    assert submodel_references_id_set == {"example_submodel_element_collection_id", "simple_submodel_element_collection_id", "example_submodel_element_collection_for_union_id"}
    assert data_model.get_referenced_models(example_aas.example_submodel.submodel_element_collection_attribute_simple) == [
    ]


def test_normalize_complex_example(
    example_aas: ValidAAS,
    referenced_aas_1: ValidAAS
):
    example_aas_list = [example_aas.model_copy(deep=True) for _ in range(3)]
    referenced_aas_1_list = [referenced_aas_1.model_copy(deep=True) for _ in range(3)]
    referenced_aas_1_list[0].id = "other_id"
    for model in referenced_aas_1_list:
        model.example_submodel = model.example_submodel.model_copy(deep=True)
    assert id(example_aas_list[0]) != id(example_aas_list[1]) and id(example_aas_list[1]) != id(example_aas_list[2]) and id(example_aas_list[0]) != id(example_aas_list[2])
    assert id(referenced_aas_1_list[0].example_submodel) != id(referenced_aas_1_list[1].example_submodel) and id(referenced_aas_1_list[1].example_submodel) != id(referenced_aas_1_list[2].example_submodel) and id(referenced_aas_1_list[0].example_submodel) != id(referenced_aas_1_list[2].example_submodel)

    normalized_list = normalize_identifiables(example_aas_list)
    assert id(normalized_list[0]) == id(normalized_list[1]) and id(normalized_list[1]) == id(normalized_list[2]) and id(normalized_list[0]) == id(normalized_list[2])
    
    normalized_referenced_aas_1_list = normalize_identifiables(referenced_aas_1_list)
    assert id(normalized_referenced_aas_1_list[0].example_submodel) == id(normalized_referenced_aas_1_list[1].example_submodel) and id(normalized_referenced_aas_1_list[1].example_submodel) == id(normalized_referenced_aas_1_list[2].example_submodel) and id(normalized_referenced_aas_1_list[0].example_submodel) == id(normalized_referenced_aas_1_list[2].example_submodel)

def test_more_complex_example(
    example_aas: ValidAAS,
    referenced_aas_1: ValidAAS,
    referenced_aas_2: ValidAAS,
    example_submodel_with_reference: ExampleSubmodelWithReference,
    example_submodel_with_id_reference: ExampleSubmodelWithIdReference,
    example_submodel_with_product_association: ExampleBasemodelWithAssociation,
    example_basemodel_with_id: ExampleBaseMdelWithId,
    example_object_with_id: ObjectBomWithId,
    example_basemodel_with_identifier_attribute: BaseModelWithIdentifierAttribute,
    example_object_with_identifier_attribute: ObjectWithIdentifierAttribute,
):
    data_model = DataModel.from_models(
        example_aas,
        referenced_aas_1,
        referenced_aas_2,
        example_submodel_with_reference,
        example_submodel_with_id_reference,
        example_submodel_with_product_association,
        example_basemodel_with_id,
        example_object_with_id,
        example_basemodel_with_identifier_attribute,
        example_object_with_identifier_attribute,
    )
    assert data_model.get_model("valid_aas_id") == example_aas
    assert data_model.get_model("example_submodel_id") == example_aas.example_submodel
    assert (
        data_model.get_model("example_basemodel_with_id")
        == example_basemodel_with_id
    )
    assert (
        data_model.get_model("example_object_with_id") == example_object_with_id
    )
    assert (
        data_model.get_model("example_basemodel_with_identifier_attribute_id")
        == example_basemodel_with_identifier_attribute
    )
    assert (
        data_model.get_model("example_object_with_identifier_attribute_id")
        == example_object_with_identifier_attribute
    )

    assert len(data_model._key_ids_models) == 17
    valid_aas_models = data_model.get_models_of_type_name("ValidAAS") 
    valid_aas_model_ids = set([get_id_with_patch(model) for model in valid_aas_models])
    assert valid_aas_model_ids == {"valid_aas_id", "referenced_aas_1_id", "referenced_aas_2_id"}
    valid_aas_models = data_model.get_models_of_type(ValidAAS)
    valid_aas_model_ids = set([get_id_with_patch(model) for model in valid_aas_models])
    assert valid_aas_model_ids == {"valid_aas_id", "referenced_aas_1_id", "referenced_aas_2_id"}
    submodel_models = data_model.get_models_of_type_name("ExampleSubmodel")
    submodel_model_ids = set([get_id_with_patch(model) for model in submodel_models])
    assert submodel_model_ids == {"example_submodel_id", "example_submodel_for_union_id", "example_optional_submodel_id"}
    submodel_models = data_model.get_models_of_type(ExampleSubmodel)
    submodel_model_ids = set([get_id_with_patch(model) for model in submodel_models])
    assert submodel_model_ids == {"example_submodel_id", "example_submodel_for_union_id", "example_optional_submodel_id"}
    submodel_2_models = data_model.get_models_of_type_name("ExampleSubmodel2")
    submodel_2_model_ids = set([get_id_with_patch(model) for model in submodel_2_models])
    assert submodel_2_model_ids == {"example_submodel_2_id"}
    assert data_model.get_models_of_type_name("ExampleSubmodelWithReference") == [
        example_submodel_with_reference
    ]
    assert data_model.get_referencing_models(example_aas) == []
    
    referencing_models = data_model.get_referencing_models(referenced_aas_1)
    referencing_model_ids = set([get_id_with_patch(model) for model in referencing_models])
    assert referencing_model_ids == {"example_submodel_with_reference_components_id", "example_submodel_with_id_reference_components_id", "example_submodel_with_product_association_id"}


    referenced_models = data_model.get_referenced_models(example_submodel_with_reference)
    assert len(referenced_models) == 2
    referenced_model_ids = set([get_id_with_patch(model) for model in referenced_models])
    assert referenced_model_ids == {"referenced_aas_1_id", "referenced_aas_2_id"}

    referenced_models = data_model.get_referenced_models(example_submodel_with_id_reference)
    assert len(referenced_models) == 2
    referenced_model_ids = set([get_id_with_patch(model) for model in referenced_models])
    assert referenced_model_ids == {"referenced_aas_1_id", "referenced_aas_2_id"}

    referenced_models = data_model.get_referenced_models(example_submodel_with_product_association)
    assert len(referenced_models) == 2
    referenced_model_ids = set([get_id_with_patch(model) for model in referenced_models])
    assert referenced_model_ids == {"referenced_aas_1_id", "referenced_aas_2_id"}

# TODO: add tests to rebuild data model with direct / indirect references / aas structure
# TODO: also add tests for subclassing Dataclass and making mixed use as data model and basemodel
# TODO: also add tests for adding / removing model instances from data model
