import asyncio
import json
import logging
from typing import Any, Dict, List, Mapping, Optional, Union
from urllib.parse import urljoin, urlparse

import aiohttp
import httpx
from pydantic import BaseModel, Field

from aas_middleware.ports.connector import Connector
from aas_middleware.ports.lifecycle import Connectable
from aas_middleware.core.errors import ConnectionError, ValidationError
from aas_middleware.domain.data_model import DataModel

logger = logging.getLogger(__name__)


class HttpConnectorConfig(BaseModel):
    """Configuration for HTTP connectors."""
    base_url: str = Field(..., description="Base URL for the HTTP endpoint")
    headers: Dict[str, str] = Field(default_factory=dict, description="Default headers")
    timeout: float = Field(default=30.0, description="Request timeout in seconds")
    max_retries: int = Field(default=3, description="Maximum number of retries")
    retry_delay: float = Field(default=1.0, description="Delay between retries in seconds")
    verify_ssl: bool = Field(default=True, description="Whether to verify SSL certificates")
    auth: Optional[Dict[str, str]] = Field(default=None, description="Authentication credentials")


class HttpInConnector(Connector[DataModel], Connectable):
    """HTTP input connector that receives data from HTTP endpoints."""
    
    def __init__(self, config: HttpConnectorConfig, data_model: type[DataModel]):
        self.config = config
        self.data_model = data_model
        self._session: Optional[aiohttp.ClientSession] = None
        self._running = False
        self._subscribers: List[asyncio.Queue] = []
        
    async def connect(self) -> None:
        """Establish HTTP connection and start listening."""
        if self._session is not None:
            return
            
        connector = aiohttp.TCPConnector(verify_ssl=self.config.verify_ssl)
        self._session = aiohttp.ClientSession(
            connector=connector,
            headers=self.config.headers,
            timeout=aiohttp.ClientTimeout(total=self.config.timeout)
        )
        
        # Start background polling if this is a polling endpoint
        if self._should_poll():
            self._running = True
            asyncio.create_task(self._poll_loop())
            
        logger.info(f"HttpInConnector connected to {self.config.base_url}")
    
    async def disconnect(self) -> None:
        """Close HTTP connection and stop listening."""
        self._running = False
        
        if self._session:
            await self._session.close()
            self._session = None
            
        logger.info(f"HttpInConnector disconnected from {self.config.base_url}")
    
    async def provide(self) -> DataModel:
        """Provide data by making a GET request to the endpoint."""
        if not self._session:
            raise ConnectionError("Connector not connected")
            
        try:
            async with self._session.get(self.config.base_url) as response:
                response.raise_for_status()
                data = await response.json()
                return self.data_model.from_dict(data)
        except aiohttp.ClientError as e:
            raise ConnectionError(f"HTTP request failed: {e}")
        except json.JSONDecodeError as e:
            raise ValidationError(f"Invalid JSON response: {e}")
        except Exception as e:
            raise ConnectionError(f"Unexpected error: {e}")
    
    async def consume(self, value: DataModel, *, meta: Optional[Mapping[str, Any]] = None) -> None:
        """Consume data by making a POST request to the endpoint."""
        if not self._session:
            raise ConnectionError("Connector not connected")
            
        try:
            payload = value.to_dict()
            if meta:
                payload["_meta"] = meta
                
            async with self._session.post(
                self.config.base_url,
                json=payload,
                headers={"Content-Type": "application/json"}
            ) as response:
                response.raise_for_status()
                logger.debug(f"Data consumed via HTTP POST: {response.status}")
        except aiohttp.ClientError as e:
            raise ConnectionError(f"HTTP POST failed: {e}")
        except Exception as e:
            raise ConnectionError(f"Unexpected error: {e}")
    
    async def receive(self):
        """Receive data as an async iterator (for streaming endpoints)."""
        if not self._session:
            raise ConnectionError("Connector not connected")
            
        # For HTTP, we'll implement a simple polling mechanism
        # In a real implementation, this might use Server-Sent Events or WebSockets
        while self._running:
            try:
                data = await self.provide()
                yield data
                await asyncio.sleep(1)  # Simple polling interval
            except Exception as e:
                logger.error(f"Error in receive loop: {e}")
                await asyncio.sleep(5)  # Longer delay on error
    
    def _should_poll(self) -> bool:
        """Determine if this endpoint should be polled."""
        # Simple heuristic: if it's a GET endpoint, we might want to poll
        return True  # For now, always poll
    
    async def _poll_loop(self):
        """Background polling loop for endpoints that need it."""
        while self._running:
            try:
                data = await self.provide()
                # Notify subscribers
                for queue in self._subscribers:
                    try:
                        queue.put_nowait(data)
                    except asyncio.QueueFull:
                        logger.warning("Subscriber queue is full, skipping notification")
                        
                await asyncio.sleep(5)  # Poll every 5 seconds
            except Exception as e:
                logger.error(f"Polling error: {e}")
                await asyncio.sleep(10)  # Longer delay on error
    
    async def subscribe(self) -> asyncio.Queue:
        """Subscribe to data updates."""
        queue = asyncio.Queue(maxsize=100)
        self._subscribers.append(queue)
        return queue
    
    async def unsubscribe(self, queue: asyncio.Queue) -> None:
        """Unsubscribe from data updates."""
        if queue in self._subscribers:
            self._subscribers.remove(queue)


class HttpOutConnector(Connector[DataModel], Connectable):
    """HTTP output connector that sends data to HTTP endpoints."""
    
    def __init__(self, config: HttpConnectorConfig, data_model: type[DataModel]):
        self.config = config
        self.data_model = data_model
        self._session: Optional[httpx.AsyncClient] = None
        
    async def connect(self) -> None:
        """Establish HTTP connection."""
        if self._session is not None:
            return
            
        self._session = httpx.AsyncClient(
            base_url=self.config.base_url,
            headers=self.config.headers,
            timeout=self.config.timeout,
            verify=self.config.verify_ssl
        )
        
        # Add authentication if provided
        if self.config.auth:
            if "username" in self.config.auth and "password" in self.config.auth:
                self._session.auth = (
                    self.config.auth["username"],
                    self.config.auth["password"]
                )
        
        logger.info(f"HttpOutConnector connected to {self.config.base_url}")
    
    async def disconnect(self) -> None:
        """Close HTTP connection."""
        if self._session:
            await self._session.aclose()
            self._session = None
            
        logger.info(f"HttpOutConnector disconnected from {self.config.base_url}")
    
    async def provide(self) -> DataModel:
        """Provide data by making a GET request to the endpoint."""
        if not self._session:
            raise ConnectionError("Connector not connected")
            
        try:
            response = await self._session.get("/")
            response.raise_for_status()
            data = response.json()
            return self.data_model.from_dict(data)
        except httpx.HTTPError as e:
            raise ConnectionError(f"HTTP request failed: {e}")
        except json.JSONDecodeError as e:
            raise ValidationError(f"Invalid JSON response: {e}")
        except Exception as e:
            raise ConnectionError(f"Unexpected error: {e}")
    
    async def consume(self, value: DataModel, *, meta: Optional[Mapping[str, Any]] = None) -> None:
        """Consume data by making a POST request to the endpoint."""
        if not self._session:
            raise ConnectionError("Connector not connected")
            
        try:
            payload = value.to_dict()
            if meta:
                payload["_meta"] = meta
                
            response = await self._session.post(
                "/",
                json=payload,
                headers={"Content-Type": "application/json"}
            )
            response.raise_for_status()
            logger.debug(f"Data consumed via HTTP POST: {response.status_code}")
        except httpx.HTTPError as e:
            raise ConnectionError(f"HTTP POST failed: {e}")
        except Exception as e:
            raise ConnectionError(f"Unexpected error: {e}")
    
    async def receive(self):
        """Receive data as an async iterator."""
        if not self._session:
            raise ConnectionError("Connector not connected")
            
        # For output connectors, we might want to listen for responses
        # This is a simplified implementation
        while True:
            try:
                data = await self.provide()
                yield data
                await asyncio.sleep(1)
            except Exception as e:
                logger.error(f"Error in receive loop: {e}")
                await asyncio.sleep(5)
