from typing import Protocol

from aas_middleware.model.data_model import DataModel

class Mapper(Protocol):
    """
    Protocol for all mappers that are used to map data models to other data models.
    """
    def map(self, data: DataModel) -> DataModel:
        """
        Map a DataModel object to another DataModel object with different types and structure.

        Args:
            data (DataModel): A data model 

        Returns:
            DataModel: The mapped data model.
        """
        ...