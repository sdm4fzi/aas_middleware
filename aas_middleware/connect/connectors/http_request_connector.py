import aiohttp


class HttpRequestConnector:
    def __init__(self, url: str):
        self.url = url
        # TODO: allow to use parameters to the send and receive functions

    async def connect(self):
        pass

    async def disconnect(self):
        pass

    async def consume(self, body: str) -> str:
        async with aiohttp.ClientSession() as session:
            async with session.post(
                self.url,
                data=body,
                headers={"Content-Type": "application/json; charset=utf-8"},
            ) as response:
                return await response.text()

    async def provide(self) -> str:
        async with aiohttp.ClientSession() as session:
            async with session.get(self.url) as response:
                return await response.text()
