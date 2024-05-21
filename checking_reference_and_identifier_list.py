from pydantic import BaseModel, ConfigDict

class FrozenModel(BaseModel):
    id: int
    name: str

    model_config = ConfigDict(frozen=True)



a = FrozenModel(id=1, name="a")
b = FrozenModel(id=2, name="b")

c = {a: "a", b: "b"}

new_a = FrozenModel(id=1, name="a")

print(c[new_a])  # prints "a"