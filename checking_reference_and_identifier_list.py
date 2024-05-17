from typing import List
from aas_middleware.model.core import Identifier, Reference
from tests.conftest import SubmodelBomWithReferenceComponents


example_sm = SubmodelBomWithReferenceComponents(
    id_short="identifier",
    components=["comp1", "compo2"],
    num_components=2
)

for name, field_info in example_sm.model_fields.items():
    print(name, field_info.annotation)
    if field_info.annotation is Identifier:
        print("found Identifier in field:", name)
    if field_info.annotation is Reference:
        print("found Reference in field:", name)
    if field_info.annotation is List[Identifier]:
        print("found Identifier list in field:", name)
    if field_info.annotation is List[Reference]:
        print("found Reference list in field:", name)