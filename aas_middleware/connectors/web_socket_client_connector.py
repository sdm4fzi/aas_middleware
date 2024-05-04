from typing import Optional

import websockets
from fastapi import HTTPException


class WebSocketClientConnector:
    def __init__(self, url: str):
        self.url = url
        self.websocket: Optional[websockets.WebSocketClientProtocol] = None

    async def connect(self):
        self.websocket = await websockets.connect(self.url)

    async def disconnect(self):
        if self.websocket:
            await self.websocket.close()
            self.websocket = None

    async def send(self, body: str) -> Optional[str]:
        if not self.websocket:
            raise HTTPException(status_code=400, detail="Websocket not connected")
        if self.websocket:
            await self.websocket.send(body)
            return "Websocket message sent"

    async def receive(self) -> Optional[str]:
        if not self.websocket:
            raise HTTPException(status_code=400, detail="Websocket not connected")
        if self.websocket:
            message = await self.websocket.recv()
            if isinstance(message, bytes):
                message = message.decode()
            return message
