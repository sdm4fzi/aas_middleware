import json
import pathlib

from basyx.aas import model
import basyx.aas.adapter.json
from pydantic import BaseModel

from aas_middleware.model.formatting.aas.convert_aas_template import convert_object_store_to_pydantic_types
from aas_middleware.model.formatting.aas.convert_pydantic_type import convert_model_to_aas_template

file_name = "idta_carbon_foot_print_submodel_template"
resources_folder = pathlib.Path(__file__).parent / "resources"

submodel_template_file_path = resources_folder / f"{file_name}.json"

with open(submodel_template_file_path, "r") as f:
    basyx_object_store = basyx.aas.adapter.json.read_aas_json_file(f)


pydantic_models = convert_object_store_to_pydantic_types(basyx_object_store)
for pydantic_model in pydantic_models:
    with open(f"{pydantic_model.__name__}_schema.json", "w") as f:
        f.write(json.dumps(pydantic_model.model_json_schema(), indent=4))

pydantic_type = pydantic_models[0]
object_store = convert_model_to_aas_template(pydantic_type)
with open(f"{file_name}_recreated.json", "w") as f:
    basyx.aas.adapter.json.write_aas_json_file(f, object_store)

pydantic_models = convert_object_store_to_pydantic_types(object_store)
for pydantic_model in pydantic_models:
    with open(f"{pydantic_model.__name__}_schema_recreated.json", "w") as f:
        f.write(json.dumps(pydantic_model.model_json_schema(), indent=4))
