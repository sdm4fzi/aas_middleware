from __future__ import annotations
from typing import List

from pydantic import BaseModel


class DataModel(BaseModel):

    _models: List[str] = []

    def __init__(self, **data):
        super().__init__(**data)

    def add_model(self, model: str):
        self._models.append(model)

    def get_models(self) -> List[str]:
        return self._models


    @classmethod
    def from_models(cls, *models, **data) -> DataModel:
        # TODO: check models
        instance = cls(**data)
        for model in models:
            instance.add_model(model)
        return instance
    

class ExampleDataModel(DataModel):
    a: str
    b: int


new_example = ExampleDataModel(a="a", b=1)
new_example.add_model("ExampleDataModel")

print(new_example)
print(new_example.get_models())

new_example2 = ExampleDataModel.from_models("ExampleDataModel", a="a", b=1)
print(new_example2)
print(new_example2.get_models())

data_model_example = DataModel.from_models("ExampleDataModel", "another one")

print(data_model_example)
print(data_model_example.get_models())

new_data_model = DataModel()
new_data_model.add_model("str")

print(new_data_model)
print(new_data_model.get_models())
