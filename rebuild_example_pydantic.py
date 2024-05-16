from __future__ import annotations
from typing import List, Optional

from pydantic import BaseModel, create_model

class Child(BaseModel):
    name: str
    age: int
    parent: str


class Parent(BaseModel):
    name: str
    age: int
    children: List[str] = []

old_example_parent = Parent(name="John", age=40, children=["Max"])
old_example_child = Child(name="Max", age=10, parent="John")

new_child_class = create_model("Child", name=(str, ...), age=(int, ...), parent=(Optional[Parent], None))
new_parent_class = create_model("Parent", name=(str, ...), age=(int, ...), children=(List[new_child_class], []))

# del new_child_class.model_fields["parent"]
# new_child_class = create_model("Child", __base__=new_child_class, parent=(Optional[new_parent_class], None))

example_child = new_child_class(name="Max", age=10)
example_parent = new_parent_class(name="John", age=40, children=[example_child.model_dump()])
example_child.parent = example_parent

print(example_parent)
print(new_parent_class.model_fields)
print(example_child)
print(new_child_class.model_fields)