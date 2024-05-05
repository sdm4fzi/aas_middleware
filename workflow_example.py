from typing import List

from pydantic import BaseModel

import uvicorn



from aas_middleware import Middleware, VERSION
middleware = Middleware()

print(VERSION)



from aas_middleware.connect.connectors.http_request_connector import HttpRequestConnector
from aas_middleware.connect.providers.base_provider import ConnectorProvider
from aas_middleware.connect.consumers.consumers import Consumer

class ProductionResource(BaseModel):
    ID: str
    description: str
    processes: List[str]
    states: List[str]

class WorkStation(BaseModel):
    id_short: str
    description: str
    work_processes: List[str]


prodsys_connector = HttpRequestConnector("http://localhost:12345/production_resource")
workstation_connector = HttpRequestConnector("http://localhost:12345/work_station")

prodsys_consumer = Consumer(
    connector=prodsys_connector,
    data_model=ProductionResource
)

mes_provider = ConnectorProvider(
    connector=workstation_connector,
    data_model=WorkStation
)

def mes_prodsys_mapper(mes_data: WorkStation):
    # TODO: use here the mapper class...
    return ProductionResource(
        ID=mes_data.id_short,
        description=mes_data.description,
        processes=mes_data.work_processes,
        states=[]
    )

@middleware.workflow(mes_provider=mes_provider, prodsys_consumer=prodsys_consumer)
async def mes_prodsys_workflow(mes_provider: ConnectorProvider, prodsys_consumer: Consumer):
    mes_data = await mes_provider.execute()
    prodsys_data = mes_prodsys_mapper(mes_data)
    print(prodsys_data.json())
    await prodsys_consumer.execute(prodsys_data)

@middleware.workflow()
async def mes_prodsys_workflow_no_args():
    mes_data = await mes_provider.execute()
    mes_provider.get_model()
    prodsys_data = mes_prodsys_mapper(mes_data)
    print(prodsys_data.json())
    await prodsys_consumer.execute(prodsys_data)



if __name__ == "__main__":    
    import uvicorn
    uvicorn.run(middleware.app, port=13000)

    
