from aas_middleware.model.data_model import DataModel

from tests.conftest import (
    ProductAas,
    SubmodelBom,
    SubmodelBomWithReferenceComponents,
    ObjectBomWithId,
    BaseModelBomWithId,
    BaseModelBomWithIdentifierAttribute,
    ObjectBomWithIdentifierAttribute,
    SubmodelBomWithIdReferenceComponents,
    SubmodelBomWithProductAssociation,
)


def test_minimal_example_with_AAS(example_aas: ProductAas):
    data_model = DataModel.from_models(example_aas)
    assert data_model.get_model("product_aas") == example_aas
    assert data_model.get_model("product_info") == example_aas.info
    assert len(data_model._models_key_id) == 4
    assert data_model.get_models_of_type_name("ProductAas") == [example_aas]
    assert data_model.get_models_of_type(ProductAas) == [example_aas]
    assert data_model.get_models_of_type_name("SubmodelBom") == [
        example_aas.example_submodel
    ]
    assert data_model.get_models_of_type(SubmodelBom) == [example_aas.example_submodel]
    assert data_model.get_referencing_models(example_aas.info) == [example_aas]
    assert data_model.get_referenced_models(example_aas.example_submodel) == []
    assert data_model.get_referenced_models(example_aas.info) == [example_aas.info.product_version]


def test_more_complex_example(
    example_aas: ProductAas,
    example_aas_comp1: ProductAas,
    example_aas_comp2: ProductAas,
    example_submodel_with_reference_components: SubmodelBomWithReferenceComponents,
    example_submodel_with_id_reference_components: SubmodelBomWithIdReferenceComponents,
    example_submodel_with_product_association: SubmodelBomWithProductAssociation,
    example_basemodel_bom_with_id: BaseModelBomWithId,
    example_object_bom_with_id: ObjectBomWithId,
    example_basemodel_bom_with_identifier_attribute: BaseModelBomWithIdentifierAttribute,
    example_object_with_identifier_attribute: ObjectBomWithIdentifierAttribute,
):
    data_model = DataModel.from_models(
        example_aas,
        example_aas_comp1,
        example_aas_comp2,
        example_submodel_with_reference_components,
        example_submodel_with_id_reference_components,
        example_submodel_with_product_association,
        example_basemodel_bom_with_id,
        example_object_bom_with_id,
        example_basemodel_bom_with_identifier_attribute,
        example_object_with_identifier_attribute,
    )
    assert data_model.get_model("product_aas") == example_aas
    assert data_model.get_model("product_info") == example_aas.info
    assert data_model.get_model("example_basemodel_bom_with_id") == example_basemodel_bom_with_id
    assert data_model.get_model("example_object_bom_with_id") == example_object_bom_with_id
    assert data_model.get_model("example_basemodel_bom_with_identifier_attribute_id") == example_basemodel_bom_with_identifier_attribute
    assert data_model.get_model("example_object_with_identifier_attribute_id") == example_object_with_identifier_attribute

    assert len(data_model._models_key_id) == 19
    assert data_model.get_models_of_type_name("ProductAas") == [
        example_aas,
        example_aas_comp1,
        example_aas_comp2,
    ]
    assert data_model.get_models_of_type(ProductAas) == [
        example_aas,
        example_aas_comp1,
        example_aas_comp2,
    ]
    assert len(data_model.get_models_of_type_name("SubmodelBom")) == 3
    assert len(data_model.get_models_of_type(SubmodelBom)) == 3
    assert data_model.get_models_of_type_name("SubmodelBomWithReferenceComponents") == [
        example_submodel_with_reference_components
    ]
    assert data_model.get_referencing_models(example_aas) == []
    assert len(data_model.get_referencing_models(example_aas_comp1)) == 3

    assert len(data_model.get_referenced_models(example_submodel_with_reference_components)) == 2
    assert len(data_model.get_referenced_models(example_submodel_with_id_reference_components)) == 2
    assert len(data_model.get_referenced_models(example_submodel_with_product_association)) == 2
    
# TODO: add tests to rebuild data model with direct / indirect references