from fastapi import HTTPException
import websockets
from typing import Optional, Callable
import anyio


class WebSocketServerConnector:
    def __init__(
        self, host: str, port: int, reply_function: Optional[Callable[[], str]] = None
    ):
        self.host = host
        self.port = port
        self.server: Optional[websockets.WebSocketServer] = None
        self.websocket: Optional[websockets.WebSocketServerProtocol] = None
        self.received_data_event = anyio.Event()
        self.received_data: str = ""
        self.reply_function = reply_function
        self.connectable = False

    async def start_server(self) -> None:
        self.server = await websockets.serve(
            self.handle_websocket, self.host, self.port
        )

    async def handle_websocket(
        self, websocket: websockets.WebSocketServerProtocol, path: str
    ) -> None:
        if not self.connectable:
            await websocket.close()
            return
        self.websocket = websocket

        try:
            async for message in websocket:
                print(f"Received message: {message}")
                if isinstance(message, bytes):
                    message = message.decode()
                self.received_data = message
                self.received_data_event.set()
                if self.reply_function:
                    await websocket.send(self.reply_function())
                else:
                    await websocket.send("Message received")

        except websockets.exceptions.ConnectionClosed:
            raise HTTPException(status_code=400, detail="Websocket connection closed.")

    async def connect(self) -> None:
        """
        Function activates that connection to the server are allowed and accepted.
        """
        if not self.server:
            raise HTTPException(
                status_code=400, detail="Websocket server is not started."
            )
        self.connectable = True
        if not self.server:
            await self.start_server()

    async def disconnect(self) -> None:
        self.connectable = False
        if self.websocket:
            await self.websocket.close()
            self.websocket = None
        if self.server:
            self.server.close()
            await self.server.wait_closed()
            self.server = None

    async def send(self, body: str) -> Optional[str]:
        if not self.server:
            raise HTTPException(
                status_code=400, detail="Websocket server is not started."
            )
        if not self.websocket:
            raise HTTPException(
                status_code=400, detail="Websocket not connected to websocket server."
            )
        await self.websocket.send(body)

    async def receive(self) -> str:
        await self.received_data_event.wait()
        self.received_data_event = anyio.Event()
        return self.received_data
