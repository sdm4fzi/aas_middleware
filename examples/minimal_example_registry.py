import json
import typing
import uvicorn
import aas_middleware
from aas_middleware.model.core import Identifiable
from aas_middleware.model.formatting.aas.basyx_formatter import BasyxTemplateFormatter


class BillOfMaterialInfo(Identifiable):
    manufacterer: str
    product_type: str


class BillOfMaterial(Identifiable):
    components: typing.List[str]
    bill_of_material_info: BillOfMaterialInfo


class ProcessModel(Identifiable):
    processes: typing.List[str]


class Product(Identifiable):
    bill_of_material: BillOfMaterial
    process_model: typing.Optional[ProcessModel]
    primitive: typing.Union[float, int]
    primitive_list: typing.List[str]
    process_model_list: typing.List[ProcessModel]


example_product = Product(
    id="example_product_id",
    bill_of_material=BillOfMaterial(
        id="example_bom_id",
        components=["component_1", "component_2"],
        bill_of_material_info=BillOfMaterialInfo(
            id="example_bom_info_id",
            manufacterer="Example Manufacterer",
            product_type="Example Product Type",
        ),
    ),
    process_model=ProcessModel(
        id="example_process_model_id",
        processes=["process_1", "process_2"]
    ),
    primitive=1.0,
    primitive_list=["1", "2"],
    process_model_list=[
        ProcessModel(
            id="example_process_model_id_1",
            processes=["process_1", "process_2"]
        ),
        ProcessModel(
            id="example_process_model_id_2",
            processes=["process_3", "process_4"]
        ),
    ],
)

data_model = aas_middleware.DataModel.from_models(example_product)
print(data_model.get_top_level_types())

middleware = aas_middleware.Middleware()
middleware.load_data_model(
    "example", data_model, persist_instances=True
)
print(data_model.get_top_level_types())

print("### REST ###")
# middleware.generate_rest_api_for_data_model("example")
# FIXME: graphql not adjusted yet to generic Object models like REST, still dependency on AAS
print("### GraphQL ###")
middleware.generate_graphql_api_for_data_model("example")
print("### Registry ###")
middleware.connect_to_registry(
    registry_type="consul",
    registry_url="http://localhost:8500",
    host="host.docker.internal",
    port=8000
)


class TrivialConnector:
    def __init__(self):
        pass

    async def connect(self):
        pass

    async def disconnect(self):
        pass

    async def consume(self, body: str) -> None:
        print(body)
        pass

    async def provide(self) -> typing.Any:
        return "trivial connector example value"


example_connector = TrivialConnector()
middleware.add_connector("test_connector", example_connector, model_type=str)


@middleware.workflow(capability="print_and_return")
def example_workflow(a: str) -> str:
    print(a)
    return a


if __name__ == "__main__":
    # uvicorn.run("minimal_example:middleware.app", reload=True)
    uvicorn.run(middleware.app)
