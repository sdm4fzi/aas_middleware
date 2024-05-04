from abc import ABC, abstractmethod
from typing import Type

from pydantic import PrivateAttr
from aas_middleware.data_model.data_model import ORIGIN_DATA_MODEL, REFERABLE_MODEL


class ReferableMapper(ABC):

    _origin_model: REFERABLE_MODEL = PrivateAttr()
    _target_model: REFERABLE_MODEL = PrivateAttr()

    def __init__(self, origin: Type[REFERABLE_MODEL], target: Type[REFERABLE_MODEL]):
        self._origin_model = origin
        self._target_model = target

    def to_origin(self, ) -> REFERABLE_MODEL:
        """
        Property to get the original model of the model.

        Returns:
            AbstractModel: The original model.
        """
        return self._origin_model

    @abstractmethod
    def to_target(self) -> REFERABLE_MODEL:
        """
        Abstract method to map the data model in the mapper from a 

        Returns:
            List[AbstractModel]: The list of flat models.
        """
        pass

    @classmethod
    @abstractmethod
    def from_origin(cls, original_model: REFERABLE_MODEL):
        """
        Class method to create a model from an original object.

        Args:
            original (object): The original object to create the model from.

        Returns:
            AbstractModel: The model created from the original object.
        """
        pass
