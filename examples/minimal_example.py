import json
import typing
import uvicorn
import aas_middleware
from aas_middleware.model.formatting.aas.basyx_formatter import BasyxTemplateFormatter


class BillOfMaterialInfo(aas_middleware.SubmodelElementCollection):
    manufacterer: str
    product_type: str


class BillOfMaterial(aas_middleware.Submodel):
    components: typing.List[str]
    bill_of_material_info: BillOfMaterialInfo


class ProcessModel(aas_middleware.Submodel):
    processes: typing.List[str]


class Product(aas_middleware.AAS):
    bill_of_material: BillOfMaterial
    process_model: typing.Optional[ProcessModel]


example_product = Product(
    id="example_product_id",
    id_short="example_product_id",
    description="Example Product",
    bill_of_material=BillOfMaterial(
        id="example_bom_id",
        id_short="example_bom_id",
        description="Example Bill of Material",
        components=["component_1", "component_2"],
        bill_of_material_info=BillOfMaterialInfo(
            id="example_bom_info_id",
            id_short="example_bom_info_id",
            description="Example Bill of Material Info",
            manufacterer="Example Manufacterer",
            product_type="Example Product Type",
        ),
    ),
    process_model=ProcessModel(
        id="example_process_model_id",
        id_short="example_process_model_id",
        description="Example Process Model",
        processes=["process_1", "process_2"]
    ),
)

data_model = aas_middleware.DataModel.from_models(example_product)
basyx_object_store = aas_middleware.formatting.BasyxFormatter().serialize(data_model)

formatter = aas_middleware.formatting.AasJsonFormatter()
json_aas = formatter.serialize(data_model)  
# with open("example_aas.json", "w") as f:
#     f.write(json.dumps(json_aas, indent=4))


infered_data_model_with_templates = BasyxTemplateFormatter().deserialize(basyx_object_store)
types = list(infered_data_model_with_templates._schemas.values())
reformatted_data_model = aas_middleware.formatting.AasJsonFormatter().deserialize(
    json_aas, types
)
print(reformatted_data_model.get_model("example_product_id"))


middleware = aas_middleware.AasMiddleware()
middleware.load_aas_persistent_data_model(
    "example", data_model, "localhost", 8081, "localhost", 8081, persist_instances=True, caching=True
)

middleware.generate_rest_api_for_data_model("example")
middleware.generate_graphql_api_for_data_model("example")


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


@middleware.workflow()
def example_workflow(a: str) -> str:
    print(a)
    return a


if __name__ == "__main__":
    # uvicorn.run("minimal_example:middleware.app", reload=True)
    uvicorn.run(middleware.app)
