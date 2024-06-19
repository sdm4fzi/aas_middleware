from typing import Any, Optional
from asyncua import Client, Node

class OpcUaConnector:
    def __init__(self, url: str, namespace: str, object_id: str, variable_id: str):
        self.url = url
        self.namespace = namespace
        self.object_id = object_id
        self.variable_id = variable_id

        self.client = None

    async def connect(self):
        self.client = Client(url=self.url)
        await self.client.connect()

    async def disconnect(self):
        await self.client.disconnect()

    async def get_node(self) -> Node:
        nsidx = await self.client.get_namespace_index(self.namespace)
        if self.variable_id:
            connection_string = (
                f"0:Objects/{nsidx}:{self.object_id}/{nsidx}:{self.variable_id}"
            )
        else:
            connection_string = f"0:Objects/{nsidx}:{self.object_id}"
        return await self.client.nodes.root.get_child(connection_string)

    async def consume(self, body: Optional[Any
    ]) -> None:
        node = await self.get_node()
        await node.write_value(body)

    async def provide(self) -> Any:
        node = await self.get_node()
        return await node.read_value()
