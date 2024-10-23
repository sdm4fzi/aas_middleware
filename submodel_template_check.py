import json

from basyx.aas import model
import basyx.aas.adapter.json
from pydantic import BaseModel

from aas_middleware.model.formatting.aas.convert_aas_template import convert_object_store_to_pydantic_types
from aas_middleware.model.formatting.aas.convert_pydantic_type import convert_model_to_aas_template
with open("idta_provisioning_of_simulation_models.json", "r") as f:
    basyx_object_store = basyx.aas.adapter.json.read_aas_json_file(f)

# for el in basyx_object_store:
#     if isinstance(el, model.Submodel) and el.kind == model.ModellingKind.TEMPLATE:
#         submodel = el
#         break
# pydantic_model = convert_submodel_template_to_pydatic_type(submodel)
# with open("idta_asset_interfaces_mapping_submodel_template_schema.json", "w") as f:
#     f.write(json.dumps(pydantic_model.model_json_schema()))
pydantic_models = convert_object_store_to_pydantic_types(basyx_object_store)
for pydantic_model in pydantic_models:
    with open(f"{pydantic_model.__name__}_schema.json", "w") as f:
        f.write(json.dumps(pydantic_model.model_json_schema()))

pydantic_type = pydantic_models[0]
object_store = convert_model_to_aas_template(pydantic_type)
with open("idta_provisioning_of_simulation_models_recreated.json", "w") as f:
    basyx.aas.adapter.json.write_aas_json_file(f, object_store)

pydantic_models = convert_object_store_to_pydantic_types(object_store)
for pydantic_model in pydantic_models:
    with open(f"{pydantic_model.__name__}_schema_recreated.json", "w") as f:
        f.write(json.dumps(pydantic_model.model_json_schema()))