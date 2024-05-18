from types import UnionType
from typing import Union
import typing
from pydantic import BaseModel

class E1(BaseModel):
    name: str
    age: int


class E2(BaseModel):
    adress: str

class E3(BaseModel):
    attr: typing.Union[E1, E2]

e1 = E1(name="peter", age=23)
e2 = E2(adress="streeeet")


e31 = E3(attr=e1)
e32 = E3(attr=e2)


for model in [e31, e32]:
    for field_name, field_info in model.model_fields.items():
        print(field_name, field_info.annotation, typing.get_origin(field_info.annotation))
        if field_info.annotation == Union:
            print("true")
        if typing.get_origin(field_info.annotation) is typing.Union:
            print("typing Union")
        if typing.get_origin(field_info.annotation) == typing.Union:
            print("typing Union equal")