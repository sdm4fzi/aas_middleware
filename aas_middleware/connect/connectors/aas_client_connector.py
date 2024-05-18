
class BasyxAASConnector:
    def __init__(self, host: str, port: int, aas_id: str):
        self.host = host
        self.port = port
        self.aas_id = aas_id

        # TODO: instantiate client here for querying the model


    async def connect(self):
        pass

    async def disconnect(self):
        pass

    async def send(self, body: str) -> str:
        # TODO: this method should do get and post!
        pass

    async def receive(self) -> str:
        pass


class BasyxSubmodelConnector:
    def __init__(self, host: str, port: int, submodel_id: str):
        self.host = host
        self.port = port
        self.submodel_id = submodel_id

        # TODO: instantiate client here for querying the model


    async def connect(self):
        pass

    async def disconnect(self):
        pass

    async def send(self, body: str) -> str:
        pass

    async def receive(self) -> str:
        pass