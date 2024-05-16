from __future__ import annotations
from typing import List, Type

from pydantic import BaseModel
import pytest

from aas_middleware.model.core import Identifier, Reference

from aas_middleware.model.formatting.aas.aas_model import AAS, Submodel, SubmodelElementCollection

class Version(SubmodelElementCollection):
    version: str
    product_type: str

class ProductInfo(Submodel):
    product_name: str
    manufacturer: str
    product_version: Version

class SubmodelBom(Submodel):
    components: List[str]
    num_components: int

class SubmodelBomWithReferenceComponents(Submodel):
    components: List[Reference]
    num_components: int

class SubmodelBomWithIdReferenceComponents(Submodel):
    component_ids: List[str]
    num_components: int

class SubmodelBomWithProductAssociation(Submodel):
    components: List[ProductAas]
    num_components: int

class ProductAas(AAS):
    example_submodel: SubmodelBom
    info: ProductInfo

class FaultyAas(AAS):
    example_string_value: str

class BaseModelBomWithId(BaseModel):
    id: str
    components: List[str]
    num_components: int


class ObjectBomWithId:
    def __init__(self, id: str, components: List[str], num_components: int):
        self.id = id
        self.components = components
        self.num_components = num_components

class BaseModelBomWithIdentifierAttribute(BaseModel):
    other_name_id_attribute: Identifier
    components: List[str]
    num_components: int
    id: str


class ObjectBomWithIdentifierAttribute:
    def __init__(self, other_name_id_attribute: Identifier, components: List[str], num_components: int, id: str):
        self.other_name_id_attribute = other_name_id_attribute
        self.components = components
        self.num_components = num_components
        self.id = id

@pytest.fixture(scope="function")
def faulty_aas() -> Type[FaultyAas]:
    return FaultyAas

@pytest.fixture(scope="function")
def example_submodel_collection() -> SubmodelElementCollection:
    return Version(
        id_short="version_info",
        version="1.2.2",
        product_type="type1"
    )

@pytest.fixture(scope="function")
def example_submodel() -> Submodel:
    return ProductInfo(
        id_short="product_info",
        product_name="product1",
        manufacturer="manufacturer1",
        product_version=Version(
            id_short="version_info",
            version="1.2.2",
            product_type="type1"
        )
    )

@pytest.fixture(scope="function")
def example_submodel_with_reference_components() -> SubmodelBomWithReferenceComponents:
    return SubmodelBomWithReferenceComponents(
        id_short="bom",
        components=["comp1", "comp2"],
        num_components=2
    )


@pytest.fixture(scope="function")
def example_aas() -> AAS:
    return ProductAas(
        id_short="product_aas",
        example_submodel=SubmodelBom(
            id_short="bom",
            components=["comp1", "comp2"],
            num_components=2
        ),
        info=ProductInfo(
            id_short="product_info",
            product_name="product1",
            manufacturer="manufacturer1",
            product_version=Version(
                id_short="version_info",
                version="1.2.2",
                product_type="type1"
            )
        )
    )

@pytest.fixture(scope="function")
def example_aas_comp1() -> AAS:
    return ProductAas(
        id_short="comp1",
        example_submodel=SubmodelBom(
            id_short="bom_comp1",
            components=[],
            num_components=0
        ),
        info=ProductInfo(
            id_short="product_info_comp1",
            product_name="productcomp1",
            manufacturer="manufacturer1",
            product_version=Version(
                id_short="version_info_comp1",
                version="1.2.2",
                product_type="type1"
            )
        )
    )

@pytest.fixture(scope="function")
def example_aas_comp2() -> AAS:
    return ProductAas(
        id_short="comp2",
        example_submodel=SubmodelBom(
            id_short="bom_comp2",
            components=[],
            num_components=0
        ),
        info=ProductInfo(
            id_short="product_info_comp2",
            product_name="productcomp2",
            manufacturer="manufacturer1",
            product_version=Version(
                id_short="version_info_comp2",
                version="1.2.2",
                product_type="type1"
            )
        )
    )

@pytest.fixture(scope="function")
def example_submodel_bom() -> SubmodelBom:
    return SubmodelBom(id="object_id", components=["comp1", "comp2"], num_components=2)

@pytest.fixture(scope="function")
def example_basemodel_bom_with_id() -> BaseModelBomWithId:
    return BaseModelBomWithId(id="object_id", components=["comp1", "comp2"], num_components=2)

@pytest.fixture(scope="function")
def example_object_bom_with_id() -> ObjectBomWithId:
    return ObjectBomWithId(id="object_id", components=["comp1", "comp2"], num_components=2)

@pytest.fixture(scope="function")
def example_basemodel_bom_with_identifier_attribute() -> BaseModelBomWithIdentifierAttribute:
    return BaseModelBomWithIdentifierAttribute(other_name_id_attribute="object_id", components=["comp1", "comp2"], num_components=2, id="id_named_attribute")

@pytest.fixture(scope="function")
def example_object_with_identifier_attribute() -> ObjectBomWithIdentifierAttribute:
    return ObjectBomWithIdentifierAttribute(other_name_id_attribute="object_id", components=["comp1", "comp2"], num_components=2, id="id_named_attribute")

