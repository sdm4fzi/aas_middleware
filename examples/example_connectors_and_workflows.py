import asyncio
import random
import typing

from pydantic import BaseModel
import aas_middleware
from aas_middleware.middleware.sync.synced_connector import SyncRole
from aas_middleware.model.mapping.mapper import Mapper


class BillOfMaterialInfo(aas_middleware.SubmodelElementCollection):
    manufacterer: str
    product_type: str

class BillOfMaterial(aas_middleware.Submodel):
    components: typing.List[str]
    bill_of_material_info: BillOfMaterialInfo

class ProductState(aas_middleware.Submodel):
    temperature: float

class Product(aas_middleware.AAS):
    bill_of_material: BillOfMaterial
    product_state: typing.Optional[ProductState] = None


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
    product_state=ProductState(
        id="example_product_state_id",
        id_short="example_product_state_id",
        description="Example Product State",
        temperature=0.0,
    ),
)

data_model = aas_middleware.DataModel.from_models(example_product)

middleware = aas_middleware.Middleware()
middleware.load_data_model("example", data_model, persist_instances=True)

# middleware = aas_middleware.AasMiddleware()
# middleware.load_aas_persistent_data_model(
#     "example", data_model, "localhost", 8081, "localhost", 8081, persist_instances=True
# )


middleware.generate_rest_api_for_data_model("example")
# middleware.generate_graphql_api_for_data_model("example")


class TrivialConnector:
    def __init__(self):
        pass

    async def connect(self):
        pass

    async def disconnect(self):
        pass

    async def consume(self, body: str) -> None:
        print("Consuming trivial connector example value:", body)
        pass

    async def provide(self) -> typing.Any:
        print("Providing trivial connector example value")
        return "trivial connector example value"
    

class TemperatureConnector:
    def __init__(self):
        self.current_temperature = 0.0

    async def connect(self):
        pass

    async def disconnect(self):
        pass

    async def provide(self) -> typing.Any:
        print("Providing temperature data:", self.current_temperature)
        return self.current_temperature
    
    async def receive(self) -> typing.Any:
        while True:
            
            self.current_temperature = random.uniform(-100, 100.0)
            print("New temperature data:", self.current_temperature)
            yield self.current_temperature
            await asyncio.sleep(1)  # Simulate a delay in receiving data



example_connector = TrivialConnector()
middleware.add_connector("test_connector", example_connector, model_type=str,)

middleware.sync_connector(connector_id="test_connector",
                        data_model_name="example",
                        model_id="example_product_id",
                        contained_model_id="example_bom_info_id",
                        field_id="manufacterer",
                        )

temperature_connector = TemperatureConnector()
middleware.add_connector("temperature_connector", temperature_connector, model_type=float)
middleware.sync_connector(connector_id="temperature_connector",
                        data_model_name="example",
                        model_id="example_product_id",
                        contained_model_id="example_product_state_id",
                        field_id="temperature",
                        sync_role=SyncRole.GROUND_TRUTH
                        )

class OtherProductModel(BaseModel):
    id: str
    id_short: str
    description: str
    manufacterer: str
    product_type: str
    components: typing.List[str]



class ExternalMapper(Mapper[OtherProductModel, Product]):
    def map(self, data: OtherProductModel) -> Product:
        return Product(
            id=data.id,
            id_short=data.id_short,
            description=data.description,
            bill_of_material=BillOfMaterial(
                id=data.id + "_bom",
                id_short=data.id + "_bom",
                components=data.components,
                bill_of_material_info=BillOfMaterialInfo(
                    id=data.id + "_bom_info",
                    id_short=data.id + "_bom_info",
                    manufacterer=data.manufacterer,
                    product_type=data.product_type,
                ),
            ),
            )
    

class PersistenceMapper(Mapper[Product, OtherProductModel]):
    def map(self, data: Product) -> OtherProductModel:
        return OtherProductModel(
            id=data.id,
            id_short=data.id_short,
            description=data.description,
            manufacterer=data.bill_of_material.bill_of_material_info.manufacterer,
            product_type=data.bill_of_material.bill_of_material_info.product_type,
            components=data.bill_of_material.components,
        )
    

old_schema_db_entry = OtherProductModel(
    id="example_product_id",
    id_short="example_product_id",
    description="Example Product",
    manufacterer="Boschlier", 
    product_type="Example Product Type",
    components=["component_1", "component_2"]
)
    

@middleware.workflow()
def get_product_information_for_manufacturer(manufacter: str) -> OtherProductModel:
    return old_schema_db_entry

middleware.connect_workflow_to_persistence_consumer("get_product_information_for_manufacturer", "example", "example_product_id", external_mapper=ExternalMapper())


@middleware.workflow()
def update_product_information_manufacterer(product: typing.Optional[Product]=None) -> OtherProductModel:
    product.bill_of_material.bill_of_material_info.manufacterer = "Siemensianer"
    return PersistenceMapper().map(product)

middleware.connect_workflow_to_persistence_provider("update_product_information_manufacterer", "product", "example", "example_product_id")


if __name__ == "__main__":
    import uvicorn


    # uvicorn.run("connections_example:middleware.app", reload=True)
    uvicorn.run(middleware.app)
