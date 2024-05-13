from typing import List, Type

from pydantic import BaseModel
import pytest

from aas_middleware.model.core import Identifier, Identifiable, get_id

from aas_middleware.model.formatting.aas.aas_model import AAS, Submodel, SubmodelElementCollection


class Version(SubmodelElementCollection):
    version: str
    product_type: str

class ProductInfo(Submodel):
    product_name: str
    manufacturer: str
    version: Version

class SubmodelBom(Submodel):
    components: List[str]
    num_components: int


class ProductAas(AAS):
    submodel_bom: SubmodelBom
    product_info: ProductInfo

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
        version=Version(
            id_short="version_info",
            version="1.2.2",
            product_type="type1"
        )
    )


@pytest.fixture(scope="function")
def example_aas() -> AAS:
    return ProductAas(
        id_short="product_aas",
        submodel_bom=SubmodelBom(
            id_short="bom",
            components=["comp1", "comp2"],
            num_components=2
        ),
        product_info=ProductInfo(
            id_short="product_info",
            product_name="product1",
            manufacturer="manufacturer1",
            version=Version(
                id_short="version_info",
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

