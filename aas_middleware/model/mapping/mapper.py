from pyexpat import model
from typing import Generic, Protocol, TypeVar
import typing

from pydantic import BaseModel

from aas_middleware.model.data_model import DataModel

T = TypeVar("T", bound=BaseModel)
S = TypeVar("S", bound=BaseModel)


@typing.runtime_checkable
class Mapper(Protocol, Generic[S, T]):
    """
    Protocol for all mappers that are used to map data models to other data models.
    """

    def map(self, data: S) -> T:
        """
        Map a DataModel object to another DataModel object with different types and structure.

        Args:
            data (DataModel): A data model

        Returns:
            DataModel: The mapped data model.
        """
        ...

if __name__ == "__main__":
    class ExampleDataModel1(DataModel):
        pass

    class ExampleDataModel2(DataModel):
        pass


    class ModelMapper(Mapper[ExampleDataModel1, ExampleDataModel2]):
        def map(self, data: ExampleDataModel1) -> ExampleDataModel2:
            return ExampleDataModel2()

    example_data_model1 = ExampleDataModel1()
    example_data_model2 = ExampleDataModel2()

    model_mapper = ModelMapper()
    mapped_model = model_mapper.map(example_data_model1)
    print(mapped_model, type(mapped_model))  # <aas_middleware.model.mapping.mapper.ExampleDataModel2 object at 0x7f8b3c3b3d30> <class 'aas_middleware.model.mapping.mapper.ExampleDataModel2'>


    print(isinstance(model_mapper, Mapper))  # True
    print(typing.get_type_hints(model_mapper.map))
    print(typing.get_type_hints(ModelMapper.map))