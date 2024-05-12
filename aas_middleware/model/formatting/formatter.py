from typing import Protocol, Any

from aas_middleware.model.data_model import DataModel


class Formatter(Protocol):
    """
    Protocol for all formatters that are used to serialize and deserialize data models.
    """

    def serialize(self, data: DataModel) -> Any:
        """
        Serialize a DataModel object to the specific format of the formatter.

        Args:
            data (DataModel): A data model

        Returns:
            Any: A string in the specific format of the formatter.
        """
        ...

    def deserialize(self, data: Any) -> DataModel:
        """
        Deserialize the specific format of the formater to a DataModel object.

        Args:
            data (Any): The specific format of the formatter.

        Returns:
            DataModel: A data model that holds the objects that were deserialized
        """
        ...
