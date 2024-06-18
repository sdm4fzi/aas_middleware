from types import UnionType
from typing import Optional, Union
import typing
from pydantic import BaseModel, model_validator

class Example(BaseModel):
    a: str
    c: Optional[int]

    @model_validator(mode="before")
    @classmethod
    def set_optional_fields_to_None(cls, data):
        for field_name, field_info in cls.model_fields.items():
            if field_name in data:
                continue
            if typing.get_origin(field_info.annotation) == Union and type(None) in typing.get_args(field_info.annotation):
                data[field_name] = None
        return data

example = Example(a="a", b=1)
print("example:", example)

example2 = Example.model_validate({"a": "a", "b": 1})
print("example2:", example2)
# example3 = Example.model_validate({"a": "a"}, strict=False)
example3 = Example.model_validate_json('{"a": "a"}', strict=False)
print("example3:", example3)
