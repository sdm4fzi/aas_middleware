# TODO: check, if the polling could be timed with an asyncio event
# -> then polling could be implemented with the same interface as event driven http_reqest_connector

import aiohttp
import anyio

from aas_middleware.connect.connectors.http_request_connector import HttpRequestConnector


class HttpPollingConnector(HttpRequestConnector):
    def __init__(self, url: str, interval: float = 1):
        self.url = url
        self.interval = interval
        self.previous_value: str = ""

    async def receive(self) -> str:
        while True:
            await anyio.sleep(self.interval)
            async with aiohttp.ClientSession() as session:
                async with session.get(self.url) as response:
                    response_test = await response.text()
                    if response_test != self.previous_value:
                        self.previous_value = response_test
                        return response_test
