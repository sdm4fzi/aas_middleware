from abc import ABC, abstractmethod

from pydantic import PrivateAttr
from aas_middleware.model.data_model import ORIGIN_DATA_MODEL, REFERABLE_MODEL


class Mapper(ABC):
    # TODO: rename this class to mapper
    """
    Abstract class for all models, with the purpose of defining the interface for all models and their required attributes.

    Args:
    """

    _origin_model: ORIGIN_DATA_MODEL = PrivateAttr()
    _target_model: REFERABLE_MODEL = PrivateAttr()

    def set_origin(self, origin_model: ORIGIN_DATA_MODEL):
        """
        Method to set the original model of the model.

        Args:
            original_model (AbstractModel): The original model to set.
        """
        self._origin_model = origin_model

    def set_target(self, target_model: REFERABLE_MODEL):
        """
        Method to set the flat model of the model.

        Args:
            flat_model (FLAT_MODEL): The flat model to set.
        """
        self._target_model = target_model

    def to_origin(self) -> ORIGIN_DATA_MODEL:
        """
        Property to get the original model of the model.

        Returns:
            AbstractModel: The original model.
        """
        return self._origin_model

    @abstractmethod
    def to_target(self) -> REFERABLE_MODEL:
        """
        Property to get all flat models of the model.

        Returns:
            List[AbstractModel]: The list of flat models.
        """
        pass

    @classmethod
    @abstractmethod
    def from_origin(cls, original_model: ORIGIN_DATA_MODEL):
        """
        Class method to create a model from an original object.

        Args:
            original (object): The original object to create the model from.

        Returns:
            AbstractModel: The model created from the original object.
        """
        pass
