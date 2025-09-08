import asyncio
import json
import logging
from typing import Any, Dict, List, Mapping, Optional, Union
from datetime import datetime

import asyncpg
from pydantic import BaseModel, Field

from aas_middleware.ports.connector import Connector
from aas_middleware.ports.lifecycle import Connectable
from aas_middleware.core.errors import ConnectionError, ValidationError, PersistenceError
from aas_middleware.domain.data_model import DataModel

logger = logging.getLogger(__name__)


class SqlConnectorConfig(BaseModel):
    """Configuration for SQL connectors."""
    host: str = Field(..., description="Database host")
    port: int = Field(default=5432, description="Database port")
    database: str = Field(..., description="Database name")
    username: str = Field(..., description="Database username")
    password: str = Field(..., description="Database password")
    table_name: str = Field(..., description="Table name for data operations")
    schema: str = Field(default="public", description="Database schema")
    ssl_mode: str = Field(default="prefer", description="SSL mode")
    pool_size: int = Field(default=10, description="Connection pool size")
    max_queries: int = Field(default=50000, description="Maximum queries per connection")
    timeout: float = Field(default=30.0, description="Query timeout in seconds")


class SqlConnector(Connector[DataModel], Connectable):
    """SQL connector that provides database persistence for data models."""
    
    def __init__(self, config: SqlConnectorConfig, data_model: type[DataModel]):
        self.config = config
        self.data_model = data_model
        self._pool: Optional[asyncpg.Pool] = None
        self._table_exists = False
        
    async def connect(self) -> None:
        """Establish database connection and ensure table exists."""
        if self._pool is not None:
            return
            
        try:
            self._pool = await asyncpg.create_pool(
                host=self.config.host,
                port=self.config.port,
                database=self.config.database,
                user=self.config.username,
                password=self.config.password,
                ssl=self.config.ssl_mode != "disable",
                min_size=1,
                max_size=self.config.pool_size,
                command_timeout=self.config.timeout
            )
            
            # Ensure table exists
            await self._ensure_table_exists()
            
            logger.info(f"SqlConnector connected to {self.config.database}.{self.config.schema}.{self.config.table_name}")
        except Exception as e:
            raise ConnectionError(f"Failed to connect to database: {e}")
    
    async def disconnect(self) -> None:
        """Close database connection."""
        if self._pool:
            await self._pool.close()
            self._pool = None
            
        logger.info(f"SqlConnector disconnected from {self.config.database}")
    
    async def provide(self) -> DataModel:
        """Provide data by retrieving the latest record from the database."""
        if not self._pool:
            raise ConnectionError("Connector not connected")
            
        try:
            async with self._pool.acquire() as conn:
                query = f"""
                    SELECT data FROM {self.config.schema}.{self.config.table_name}
                    ORDER BY created_at DESC
                    LIMIT 1
                """
                row = await conn.fetchrow(query)
                
                if row is None:
                    # Return empty data model if no data exists
                    return self.data_model()
                    
                data = row['data']
                if isinstance(data, str):
                    data = json.loads(data)
                    
                return self.data_model.from_dict(data)
        except Exception as e:
            raise PersistenceError(f"Failed to retrieve data: {e}")
    
    async def consume(self, value: DataModel, *, meta: Optional[Mapping[str, Any]] = None) -> None:
        """Consume data by storing it in the database."""
        if not self._pool:
            raise ConnectionError("Connector not connected")
            
        try:
            async with self._pool.acquire() as conn:
                data_dict = value.to_dict()
                if meta:
                    data_dict["_meta"] = meta
                    
                # Convert to JSON for storage
                data_json = json.dumps(data_dict)
                
                query = f"""
                    INSERT INTO {self.config.schema}.{self.config.table_name}
                    (data, created_at, meta)
                    VALUES ($1, $2, $3)
                """
                
                await conn.execute(
                    query,
                    data_json,
                    datetime.utcnow(),
                    json.dumps(meta) if meta else None
                )
                
                logger.debug(f"Data consumed and stored in database")
        except Exception as e:
            raise PersistenceError(f"Failed to store data: {e}")
    
    async def receive(self):
        """Receive data as an async iterator, monitoring for new records."""
        if not self._pool:
            raise ConnectionError("Connector not connected")
            
        last_id = 0
        
        while True:
            try:
                async with self._pool.acquire() as conn:
                    query = f"""
                        SELECT id, data FROM {self.config.schema}.{self.config.table_name}
                        WHERE id > $1
                        ORDER BY id ASC
                    """
                    rows = await conn.fetch(query, last_id)
                    
                    for row in rows:
                        last_id = row['id']
                        data = row['data']
                        if isinstance(data, str):
                            data = json.loads(data)
                            
                        yield self.data_model.from_dict(data)
                        
                # Wait before checking for new data
                await asyncio.sleep(1)
            except Exception as e:
                logger.error(f"Error in receive loop: {e}")
                await asyncio.sleep(5)
    
    async def _ensure_table_exists(self) -> None:
        """Ensure the required table exists in the database."""
        if self._table_exists:
            return
            
        try:
            async with self._pool.acquire() as conn:
                # Check if table exists
                query = """
                    SELECT EXISTS (
                        SELECT FROM information_schema.tables 
                        WHERE table_schema = $1 AND table_name = $2
                    )
                """
                exists = await conn.fetchval(query, self.config.schema, self.config.table_name)
                
                if not exists:
                    # Create table
                    create_query = f"""
                        CREATE TABLE IF NOT EXISTS {self.config.schema}.{self.config.table_name} (
                            id SERIAL PRIMARY KEY,
                            data JSONB NOT NULL,
                            created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
                            meta JSONB
                        )
                    """
                    await conn.execute(create_query)
                    
                    # Create indexes for better performance
                    await conn.execute(f"""
                        CREATE INDEX IF NOT EXISTS idx_{self.config.table_name}_created_at 
                        ON {self.config.schema}.{self.config.table_name} (created_at)
                    """)
                    
                    logger.info(f"Created table {self.config.schema}.{self.config.table_name}")
                
                self._table_exists = True
        except Exception as e:
            raise ConnectionError(f"Failed to ensure table exists: {e}")
    
    async def query(self, sql: str, *args) -> List[Dict[str, Any]]:
        """Execute a custom SQL query."""
        if not self._pool:
            raise ConnectionError("Connector not connected")
            
        try:
            async with self._pool.acquire() as conn:
                rows = await conn.fetch(sql, *args)
                return [dict(row) for row in rows]
        except Exception as e:
            raise PersistenceError(f"Query execution failed: {e}")
    
    async def count(self) -> int:
        """Get the total count of records in the table."""
        if not self._pool:
            raise ConnectionError("Connector not connected")
            
        try:
            async with self._pool.acquire() as conn:
                query = f"SELECT COUNT(*) FROM {self.config.schema}.{self.config.table_name}"
                return await conn.fetchval(query)
        except Exception as e:
            raise PersistenceError(f"Count query failed: {e}")
    
    async def clear(self) -> None:
        """Clear all data from the table."""
        if not self._pool:
            raise ConnectionError("Connector not connected")
            
        try:
            async with self._pool.acquire() as conn:
                query = f"DELETE FROM {self.config.schema}.{self.config.table_name}"
                await conn.execute(query)
                logger.info(f"Cleared all data from {self.config.schema}.{self.config.table_name}")
        except Exception as e:
            raise PersistenceError(f"Clear operation failed: {e}")
