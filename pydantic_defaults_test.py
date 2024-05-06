from typing import List

from pydantic import BaseModel
from aas_middleware.model.core import AAS, Submodel, SubmodelElementCollection

# class BOM(Submodel):
#     """
#     Class that represents a Bill of Material (BOM).
#     """
#     components: List[str]
#     num_components: int

class NonSubmodelBom(BaseModel):
    id: str
    components: List[str]
    num_components: int

class Product(AAS):
    """
    Class that represents a product.
    """
    bom: NonSubmodelBom

example_bom = NonSubmodelBom(id="bom1", components=["comp1", "comp2"], num_components=2)
example_product = Product(id="prod1", bom=example_bom)