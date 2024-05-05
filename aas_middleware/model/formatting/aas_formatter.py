from typing import Any

import basyx.aas
from aas_middleware.model.data_model import DataModel

from basyx.aas.model import AssetAdministrationShell, Submodel, DictObjectStore

BasyxModels = AssetAdministrationShell | Submodel | DictObjectStore

# TODO: use here the classes from data_model for the AAS (Referable etc.)


class AASFormatter:
    """
    Allows to serialize and deserialize Basyx AAS objects (AssetAdministrationShells, Submodels or Containers of both) to a DataModel.
    """

    def serialize(self, data: DataModel) -> BasyxModels:
        """
        Serialize a DataModel object to the specific format of the formatter.

        Args:
            data (DataModel): A data model

        Returns:
            Any: A string in the specific format of the formatter.
        """
        # TODO: Implement the serialization
        # 1. check at first if the aas data structure can be inferred from the data model (either use correct types or data structure allows to infer the type (AAS, SM or SME))
        # 1.1 AAS only have other objects or references to them as attributes
        # 1.2 Submodels can have objects and primitive attributes, however, they never are without a parent aas
        # 1.3 all references have to be resolved to the actual object or it is an external link (valid URL)
        # 2. convert at first submodels, then aas
        pass

    def deserialize(self, data: BasyxModels) -> DataModel:
        """
        Deserialize the specific format of the formater to a DataModel object.

        Args:
            data (Any): The specific format of the formatter.

        Returns:
            DataModel: A data model that holds the objects that were deserialized
        """
        # TODO: Implement the deserialization
        # 1. check at first if meta data is available in the aas for transformation (either concept description or administrative information or submodel template)
        # 2. convert at submodels, then aas
