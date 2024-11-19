from aas_middleware.model.data_model import DataModel


from aas_middleware.model.formatting.json_schema.json_schema_to_pydantic_formatter import JsonSchemaFormatter
from aas_middleware.model.formatting.util import compare_schemas
from tests.conftest import (
    ValidAAS,
    ExampleSubmodelWithReference,
    ObjectBomWithId,
    ExampleBaseMdelWithId,
    BaseModelWithIdentifierAttribute,
    ObjectWithIdentifierAttribute,
    ExampleSubmodelWithIdReference,
    ExampleBasemodelWithAssociation,
)


def test_minimal_example(example_aas: ValidAAS):
    data_model = DataModel.from_models(example_aas)
    json_schema = JsonSchemaFormatter().serialize(data_model)
    dynamic_model = JsonSchemaFormatter().deserialize(json_schema)
    dynamic_top_level_types = dynamic_model.get_top_level_types()
    assert len(dynamic_top_level_types) == 1
    dynamic_valid_aas = dynamic_top_level_types[0]
    assert compare_schemas(example_aas.model_json_schema(), dynamic_valid_aas.model_json_schema())

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
        # example_object_with_id,
        example_basemodel_with_identifier_attribute,
        # example_object_with_identifier_attribute,
    )
    json_schema = JsonSchemaFormatter().serialize(data_model)
    dynamic_model = JsonSchemaFormatter().deserialize(json_schema)
    dynamic_top_level_types = dynamic_model.get_top_level_types()
    assert len(dynamic_top_level_types) == 6
    input_types = {
        "ValidAAS": example_aas,
        "ExampleSubmodelWithReference": example_submodel_with_reference,
        "ExampleSubmodelWithIdReference": example_submodel_with_id_reference,
        "ExampleBasemodelWithAssociation": example_submodel_with_product_association,
        "ExampleBaseMdelWithId": example_basemodel_with_id,
        "BaseModelWithIdentifierAttribute": example_basemodel_with_identifier_attribute,
    }
    for dynamic_type in dynamic_top_level_types:
        assert dynamic_type.__name__ in input_types
        assert compare_schemas(
            input_types[dynamic_type.__name__].model_json_schema(),
            dynamic_type.model_json_schema(),
            # TODO: Fix this when datamodel-code-generator transforms tuples correctly with all type hints...
            ignore_tuple_type_hints=True,
        )
