from typing import List

from pydantic import BaseModel

from aas_middleware.model.core import Identifier, Identifiable, get_id

from aas_middleware.model.formatting.aas.aas_model import AAS, Submodel, SubmodelElementCollection

class BOM(Submodel):
    components: List[str]
    num_components: int

class NonSubmodelBom(BaseModel):
    id: str
    components: List[str]
    num_components: int


class ObjectBom:
    def __init__(self, id: str, components: List[str], num_components: int):
        self.id = id
        self.components = components
        self.num_components = num_components

class IdentifierBaseModel(BaseModel):
    other_name_id_attribute: Identifier
    components: List[str]
    num_components: int


class IdentifierObject:
    def __init__(self, other_name_id_attribute: Identifier, components: List[str], num_components: int):
        self.other_name_id_attribute = other_name_id_attribute
        self.components = components
        self.num_components = num_components

class Product(AAS):
    """
    Class that represents a product.
    """
    submodel_bom: BOM
    non_submodel_bom: NonSubmodelBom
    # object_bom: ObjectBom




example_submodel_bom = BOM(id="submodel_bom", components=["comp1", "comp2"], num_components=2)
example_non_submodel_bom = NonSubmodelBom(id="non_submodel_bom", components=["comp1", "comp2"], num_components=2)
example_object_bom = ObjectBom(id="object_bom", components=["comp1", "comp2"], num_components=2)
example_identifier_basemodel = IdentifierBaseModel(other_name_id_attribute="id", components=["comp1", "comp2"], num_components=2)
example_identifier_object = IdentifierObject(other_name_id_attribute="id", components=["comp1", "comp2"], num_components=2)

example_product = Product(id="prod1", submodel_bom=example_submodel_bom, non_submodel_bom=example_non_submodel_bom)

print(get_id(example_product))
print(get_id(example_submodel_bom))
print(get_id(example_non_submodel_bom))
print(get_id(example_object_bom))
print(get_id(example_identifier_object))
print(get_id(example_identifier_basemodel))
print(get_id(example_submodel_bom.model_dump()))
# below is a value error
# print(get_id(example_identifier_basemodel.model_dump()))


Identifiable.model_validate(example_product)
Identifiable.model_validate(example_submodel_bom)
Identifiable.model_validate(example_non_submodel_bom)
Identifiable.model_validate(example_object_bom)
Identifiable.model_validate(example_identifier_object)
Identifiable.model_validate(example_identifier_basemodel)
Identifiable.model_validate(example_submodel_bom.model_dump())