from typing import Any
import aiohttp


class HttpRequestConnectorAuth:
    def __init__(self, url: str, auth_url: str, authentication_payload: Any):
        self.url = url
        self.auth_url = auth_url
        self.authentication_payload = authentication_payload
        

    async def connect(self):
        async with aiohttp.ClientSession() as session:
            async with session.post(
                self.auth_url,
                data=self.authentication_payload,
            ) as response:
                token = await response.json()
        if not response.status == 200:
            raise Exception(f"Failed to authenticate with status code {response.status} and content {await response.text()}")

        # TODO: check, how often this is used or if a more flexible methodology is required....
        self.authentication_headers = {
            "Content-Type": "application/json; charset=utf-8",
            "Authorization": f"Bearer {token["access_token"]}"
        }

    async def disconnect(self):
        pass

    async def consume(self, body: str) -> str:
        async with aiohttp.ClientSession() as session:
            async with session.post(
                self.url,
                data=body,
                headers=self.authentication_headers,
            ) as response:
                return await response.text()

    async def provide(self) -> str:
        async with aiohttp.ClientSession() as session:
            async with session.get(self.url, headers=self.authentication_headers) as response:
                return await response.json()
