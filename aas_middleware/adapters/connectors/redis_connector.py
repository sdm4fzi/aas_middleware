import asyncio
import json
import logging
from typing import Any, Dict, List, Mapping, Optional, Union
from datetime import datetime, timedelta

import aioredis
from pydantic import BaseModel, Field

from aas_middleware.ports.connector import Connector
from aas_middleware.ports.lifecycle import Connectable
from aas_middleware.core.errors import ConnectionError, ValidationError, PersistenceError
from aas_middleware.domain.data_model import DataModel

logger = logging.getLogger(__name__)


class RedisConnectorConfig(BaseModel):
    """Configuration for Redis connectors."""
    host: str = Field(default="localhost", description="Redis host")
    port: int = Field(default=6379, description="Redis port")
    database: int = Field(default=0, description="Redis database number")
    password: Optional[str] = Field(default=None, description="Redis password")
    key_prefix: str = Field(default="aas:", description="Key prefix for all operations")
    default_ttl: Optional[int] = Field(default=None, description="Default TTL in seconds")
    max_connections: int = Field(default=10, description="Maximum connection pool size")
    timeout: float = Field(default=30.0, description="Operation timeout in seconds")
    ssl: bool = Field(default=False, description="Whether to use SSL connection")


class RedisConnector(Connector[DataModel], Connectable):
    """Redis connector that provides in-memory persistence for data models."""
    
    def __init__(self, config: RedisConnectorConfig, data_model: type[DataModel]):
        self.config = config
        self.data_model = data_model
        self._redis: Optional[aioredis.Redis] = None
        self._pubsub: Optional[aioredis.client.PubSub] = None
        self._running = False
        
    async def connect(self) -> None:
        """Establish Redis connection."""
        if self._redis is not None:
            return
            
        try:
            self._redis = aioredis.from_url(
                f"redis://{self.config.host}:{self.config.port}/{self.config.database}",
                password=self.config.password,
                encoding="utf-8",
                decode_responses=True,
                max_connections=self.config.max_connections,
                socket_timeout=self.config.timeout,
                socket_connect_timeout=self.config.timeout,
                ssl=self.config.ssl
            )
            
            # Test connection
            await self._redis.ping()
            
            # Setup pubsub for real-time updates
            self._pubsub = self._redis.pubsub()
            await self._pubsub.subscribe(f"{self.config.key_prefix}updates")
            
            # Start listening for updates
            self._running = True
            asyncio.create_task(self._listen_for_updates())
            
            logger.info(f"RedisConnector connected to {self.config.host}:{self.config.port}")
        except Exception as e:
            raise ConnectionError(f"Failed to connect to Redis: {e}")
    
    async def disconnect(self) -> None:
        """Close Redis connection."""
        self._running = False
        
        if self._pubsub:
            await self._pubsub.close()
            self._pubsub = None
            
        if self._redis:
            await self._redis.close()
            self._redis = None
            
        logger.info(f"RedisConnector disconnected from Redis")
    
    async def provide(self) -> DataModel:
        """Provide data by retrieving the latest record from Redis."""
        if not self._redis:
            raise ConnectionError("Connector not connected")
            
        try:
            # Get the latest data using sorted set
            latest_key = await self._redis.zrevrange(
                f"{self.config.key_prefix}timeline",
                0, 0, withscores=True
            )
            
            if not latest_key:
                # Return empty data model if no data exists
                return self.data_model()
                
            key = latest_key[0][0]
            data_json = await self._redis.get(key)
            
            if not data_json:
                return self.data_model()
                
            data = json.loads(data_json)
            return self.data_model.from_dict(data)
        except Exception as e:
            raise PersistenceError(f"Failed to retrieve data: {e}")
    
    async def consume(self, value: DataModel, *, meta: Optional[Mapping[str, Any]] = None) -> None:
        """Consume data by storing it in Redis."""
        if not self._redis:
            raise ConnectionError("Connector not connected")
            
        try:
            data_dict = value.to_dict()
            if meta:
                data_dict["_meta"] = meta
                
            # Convert to JSON for storage
            data_json = json.dumps(data_dict)
            
            # Generate unique key
            timestamp = datetime.utcnow().timestamp()
            key = f"{self.config.key_prefix}data:{timestamp}"
            
            # Store data
            await self._redis.set(key, data_json)
            
            # Add to timeline sorted set
            await self._redis.zadd(f"{self.config.key_prefix}timeline", {key: timestamp})
            
            # Set TTL if configured
            if self.config.default_ttl:
                await self._redis.expire(key, self.config.default_ttl)
                await self._redis.expire(f"{self.config.key_prefix}timeline", self.config.default_ttl)
            
            # Publish update notification
            await self._redis.publish(
                f"{self.config.key_prefix}updates",
                json.dumps({"action": "store", "key": key, "timestamp": timestamp})
            )
            
            logger.debug(f"Data consumed and stored in Redis with key: {key}")
        except Exception as e:
            raise PersistenceError(f"Failed to store data: {e}")
    
    async def receive(self):
        """Receive data as an async iterator, monitoring for new records."""
        if not self._redis:
            raise ConnectionError("Connector not connected")
            
        last_timestamp = 0
        
        while self._running:
            try:
                # Get new data since last timestamp
                new_keys = await self._redis.zrangebyscore(
                    f"{self.config.key_prefix}timeline",
                    last_timestamp + 0.001,  # Small offset to avoid duplicates
                    "+inf"
                )
                
                for key in new_keys:
                    try:
                        data_json = await self._redis.get(key)
                        if data_json:
                            data = json.loads(data_json)
                            yield self.data_model.from_dict(data)
                            
                            # Update last timestamp
                            score = await self._redis.zscore(f"{self.config.key_prefix}timeline", key)
                            if score:
                                last_timestamp = max(last_timestamp, score)
                    except Exception as e:
                        logger.error(f"Error processing key {key}: {e}")
                        
                # Wait before checking for new data
                await asyncio.sleep(0.5)
            except Exception as e:
                logger.error(f"Error in receive loop: {e}")
                await asyncio.sleep(5)
    
    async def _listen_for_updates(self):
        """Listen for Redis pubsub updates."""
        while self._running:
            try:
                message = await self._pubsub.get_message(ignore_subscribe_messages=True)
                if message and message["type"] == "message":
                    # Handle update notification
                    try:
                        data = json.loads(message["data"])
                        logger.debug(f"Received update notification: {data}")
                    except json.JSONDecodeError:
                        logger.warning("Invalid JSON in update notification")
                        
                await asyncio.sleep(0.1)
            except Exception as e:
                logger.error(f"Error in pubsub listener: {e}")
                await asyncio.sleep(1)
    
    async def get_by_key(self, key: str) -> Optional[DataModel]:
        """Get data by specific key."""
        if not self._redis:
            raise ConnectionError("Connector not connected")
            
        try:
            data_json = await self._redis.get(key)
            if not data_json:
                return None
                
            data = json.loads(data_json)
            return self.data_model.from_dict(data)
        except Exception as e:
            raise PersistenceError(f"Failed to retrieve data by key: {e}")
    
    async def set_by_key(self, key: str, value: DataModel, ttl: Optional[int] = None) -> None:
        """Set data by specific key."""
        if not self._redis:
            raise ConnectionError("Connector not connected")
            
        try:
            data_json = json.dumps(value.to_dict())
            await self._redis.set(key, data_json)
            
            if ttl:
                await self._redis.expire(key, ttl)
            elif self.config.default_ttl:
                await self._redis.expire(key, self.config.default_ttl)
                
            logger.debug(f"Data set with key: {key}")
        except Exception as e:
            raise PersistenceError(f"Failed to set data by key: {e}")
    
    async def delete_by_key(self, key: str) -> None:
        """Delete data by specific key."""
        if not self._redis:
            raise ConnectionError("Connector not connected")
            
        try:
            await self._redis.delete(key)
            await self._redis.zrem(f"{self.config.key_prefix}timeline", key)
            logger.debug(f"Data deleted with key: {key}")
        except Exception as e:
            raise PersistenceError(f"Failed to delete data by key: {e}")
    
    async def list_keys(self, pattern: str = "*") -> List[str]:
        """List keys matching a pattern."""
        if not self._redis:
            raise ConnectionError("Connector not connected")
            
        try:
            full_pattern = f"{self.config.key_prefix}{pattern}"
            keys = await self._redis.keys(full_pattern)
            return [key.replace(self.config.key_prefix, "") for key in keys]
        except Exception as e:
            raise PersistenceError(f"Failed to list keys: {e}")
    
    async def count(self) -> int:
        """Get the total count of records."""
        if not self._redis:
            raise ConnectionError("Connector not connected")
            
        try:
            return await self._redis.zcard(f"{self.config.key_prefix}timeline")
        except Exception as e:
            raise PersistenceError(f"Count operation failed: {e}")
    
    async def clear(self) -> None:
        """Clear all data."""
        if not self._redis:
            raise ConnectionError("Connector not connected")
            
        try:
            # Get all keys
            keys = await self._redis.keys(f"{self.config.key_prefix}*")
            if keys:
                await self._redis.delete(*keys)
                
            logger.info("Cleared all data from Redis")
        except Exception as e:
            raise PersistenceError(f"Clear operation failed: {e}")
    
    async def set_ttl(self, key: str, ttl: int) -> None:
        """Set TTL for a specific key."""
        if not self._redis:
            raise ConnectionError("Connector not connected")
            
        try:
            await self._redis.expire(key, ttl)
            logger.debug(f"Set TTL for key {key}: {ttl} seconds")
        except Exception as e:
            raise PersistenceError(f"Failed to set TTL: {e}")
