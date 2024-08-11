import typing
import aas_middleware


class BillOfMaterialInfo(aas_middleware.SubmodelElementCollection):
    manufacterer: str
    product_type: str

class ExampleSEC1(aas_middleware.SubmodelElementCollection):
    attr1: int


class ExampleSEC2(aas_middleware.SubmodelElementCollection):
    attr2: int

class BillOfMaterial(aas_middleware.Submodel):
    components: typing.List[str]
    bill_of_material_info: typing.Optional[BillOfMaterialInfo]
    union_example: typing.Union[ExampleSEC1, ExampleSEC2]


class ProcessModel(aas_middleware.Submodel):
    processes: typing.List[str]


class ExampleSM1(aas_middleware.Submodel):
    attr1: int


class ExampleSM2(aas_middleware.Submodel):
    attr2: int

class Product(aas_middleware.AAS):
    bill_of_material: BillOfMaterial
    process_model: typing.Optional[ProcessModel]
    union_example_sm: typing.Union[ExampleSM1, ExampleSM2]


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
        union_example=ExampleSEC1(
            id="example_sec1_id",
            id_short="example_sec1_id",
            description="Example SEC1",
            attr1=1,
        ),
    ),
    process_model=ProcessModel(
        id="example_process_model_id",
        id_short="example_process_model_id",
        description="Example Process Model",
        processes=["process_1", "process_2"],
    ),
    union_example_sm=ExampleSM1(
        id="example_sm1_id",
        id_short="example_sm1_id",
        description="Example SM1",
        attr1=1,
    ),
    
)

data_model = aas_middleware.DataModel.from_models(example_product)


basyx_object_store = aas_middleware.formatting.BasyxFormatter().serialize(data_model)

json_aas = aas_middleware.formatting.AasJsonFormatter().serialize(data_model)
# print(json_aas)

reformatted_data_model = aas_middleware.formatting.AasJsonFormatter().deserialize(json_aas)
print(reformatted_data_model.get_model("example_product_id"))



# middleware = aas_middleware.Middleware()
# middleware.load_data_model("example", data_model, persist_instances=True)

middleware = aas_middleware.AasMiddleware()
middleware.load_aas_persistent_data_model(
    "example", data_model, "localhost", 8081, "localhost", 8081, persist_instances=True
)

middleware.generate_rest_api_for_data_model("example")
middleware.generate_graphql_api_for_data_model("example")

if __name__ == "__main__":
    import uvicorn


    uvicorn.run("optional_example:middleware.app", reload=True)
    # uvicorn.run(middleware.app)
