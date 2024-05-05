from typing import Optional
import aiohttp
import anyio
from fastapi import HTTPException


class WebHookClientConnector:
    """
    Class for a WebHookClientConnector that can be used to connect to a webhook and receive data from it.

    Args:
        web_hook_url (str): adress of the webhook

    Attributes:
        web_hook_url (str): adress of the webhook server
        own_url (Optional[str]): own url where the webhook sends data to
        hook (Optional[anyio.Event]): hook event for posts of the webhook
        connected_subscriber (Optional[str]): adress of the subscriber that is connected to the webhook
        received_data (str): data received from the webhook
    """
    def __init__(self, web_hook_url: str):
        """
        Args:
            web_hook_url (str): adress of the webhook
        """
        self.web_hook_url = web_hook_url
        self.own_url: Optional[str] = None
        self.hook: Optional[anyio.Event] = None
        self.connected_subscriber: Optional[str] = None
        self.received_data: str = ""

    async def set_hook(self, hook: anyio.Event, url: str):
        """
        Function sets the hook event for posts of the webhook and the url where the webhook should post to.
        """
        # TODO: set this hook when adding the hook to a provider so that it is linked to fastAPI post route of the datamodel
        # either to this with a callback or these events.
        self.hook = hook
        self.own_url = url

    async def trigger_hook(self, body: str):
        """
        Function triggers the hook for the webhook.
        """
        if not self.hook:
            raise HTTPException(
                status_code=400,
                detail="Webhook does not have a hook set. Please use the set_hook function to set the hook.",
            )
        self.received_data = body
        self.hook.set()

    async def connect(self):
        """
        Function connects to the webhook with a post request that sends the middleware url to the webhook.
        """
        async with aiohttp.ClientSession() as session:
            async with session.post(
                self.web_hook_url, json={"url": self.own_url}
            ) as response:
                status = response.status
                if status != 200:
                    raise HTTPException(
                        status_code=400,
                        detail="Webhook could not connect to the webhook server.",
                    )
                # TODO: add logging for somethink like this!
                await response.text()

    async def disconnect(self):
        """
        Function disconnects from the webhook. 
        """
        # TODO: either remove the hookevent from the provider or set it to false or 
        # remove the callback from the endpoint of the provider

    async def send(self, body: str) -> str:
        raise NotImplementedError(
            "WebHookClientConnector does not support sending data but only receiving data. Try to use the WebHookServerConnector instead."
        )

    async def receive(self) -> str:
        """
        Function receives data from the webhook.

        """
        if not self.hook:
            raise Exception(
                "WebHookClientConnector does not have a hook set. Please use the set_hook function to set the hook."
            )
        await self.hook.wait()
        self.hook = anyio.Event()
        return self.received_data
