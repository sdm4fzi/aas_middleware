import asyncio
import random
import typing

import aas_middleware
from aas_middleware.middleware.persistence_factory import PersistenceFactory

class Temperature(aas_middleware.Submodel):
    temperature: float

class Product(aas_middleware.AAS):
    temperature_submodel: Temperature

example_product = Product(
    id="example_product_id",
    id_short="example_product_id",
    description="Example Product",
    temperature_submodel=Temperature(
        id="example_temperature_id",
        id_short="example_temperature_id",
        temperature=0.0,
    ),
)

data_model = aas_middleware.DataModel.from_models(example_product)

middleware = aas_middleware.Middleware()
middleware.load_data_model("example", data_model, persist_instances=True)

class PersistenceConnector:
    def __init__(self, model: Product):
        self.model = model

    async def connect(self):
        pass

    async def disconnect(self):
        pass

    async def consume(self, body: Product) -> None:
        print("Consuming persistence connector example value:", body)
        self.model = body

    async def provide(self) -> Product:
        print("Providing persistence connector example value:", self.model)
        return self.model

    async def receive(self) -> typing.AsyncGenerator[float, None]:
        count = 0
        while True:
            temperature = random.uniform(5, 100.0)
            count += 1
            if count > 10:
                raise Exception("Test exception")
            self.model.temperature_submodel.temperature = temperature
            print("New temperature data:", temperature)
            yield self.model
            await asyncio.sleep(1)

persistence_factory = PersistenceFactory(PersistenceConnector)

middleware.add_default_persistence(persistence_factory, "example", None, Product)
middleware.generate_rest_api_for_data_model("example")

if __name__ == "__main__":
    import uvicorn

    # uvicorn.run("connections_example:middleware.app", reload=True)
    uvicorn.run(middleware.app)
