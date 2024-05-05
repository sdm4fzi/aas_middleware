from typing import List
import aiohttp
import anyio
from fastapi import HTTPException


class WebHookServerConnector:
    def __init__(self):
        self.hook: anyio.Event = anyio.Event()
        self.connected_subscribers: List[str] = []
        self.received_data: str = ""
        self.connectable: bool = False

    async def start_server(self) -> None:
        """
        Acticates an endpoint where clients can connect to with a post request that sends the url to post the webhook data to.
        """
        # TODO: add functionality that when added to a consumer, an endpoint is created for webhook clients to connect to.
        # and one endpoint to remove client subsciptions. THe register and unregister functions should then be used.
        pass

    async def register_subscriber(self, url: str) -> None:
        """
        Function registers a subscriber to the webhook.

        Args:
            url (str): _description_
        """
        if not self.connectable:
            raise HTTPException(status_code=400, detail="Webhook not connectable.")
        self.connected_subscribers.append(url)

    async def unregister_subscriber(self, url: str) -> None:
        """
        Function unregisters a subscriber from the webhook.

        Args:
            url (str): _description_
        """
        try:
            self.connected_subscribers.remove(url)
        except ValueError:
            raise HTTPException(status_code=400, detail="Subscriber not registered.")

    async def connect(self):
        """
        Function allows clients to connect to the webhook.
        """
        self.connectable = True

    async def disconnect(self):
        """
        Function disconnects all subscribed clients from the webhook.
        """
        self.connectable = False
        self.connected_subscribers = []

    async def send(self) -> str:
        """
        Function sends data to all subscribed clients of the webhook.

        Args:
            body (str): _description_

        Returns:
            str: _description_
        """
        await self.hook.wait()
        if not self.connectable:
            raise HTTPException(status_code=400, detail="Webhook not connectable.")
        self.hook.set()
        for subscriber in self.connected_subscribers:
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    subscriber, data=self.received_data
                ) as response:
                    await response.text()
        return "Webhook message sent"

    async def receive(self) -> str:
        raise NotImplementedError
