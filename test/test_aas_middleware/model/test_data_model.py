""" tests for the following:
- instantiate data model with pydantic models and normal classes (bad and good case)
- use all util functions (get references, models of type etc.)
- rebuild data model with direct / indirect references
"""
from h11 import Data
from aas_middleware.model.formatting.aas.aas_model import AAS, Submodel, SubmodelElementCollection
from aas_middleware.model.data_model import DataModel

def test_minimal_example_with_AAS(example_aas: AAS):
    data_model = DataModel.from_models(example_aas)
    assert data_model.get_model("product_aas") == example_aas
    assert data_model.get_model("product_info") == example_aas.info