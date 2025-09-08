import pytest
import asyncio
import json
from unittest.mock import AsyncMock, MagicMock, patch
from datetime import datetime

from aas_middleware.adapters.connectors import (
    MemoryConnector,
    HttpInConnector,
    HttpOutConnector,
    HttpConnectorConfig,
    SqlConnector,
    SqlConnectorConfig,
    RedisConnector,
    RedisConnectorConfig
)
from aas_middleware.domain.data_model import DataModel
from aas_middleware.core.errors import ConnectionError, ValidationError, PersistenceError


# Test data model
class TestDataModel(DataModel):
    name: str = "test"
    value: int = 42
    timestamp: str = "2024-01-01T00:00:00Z"


class TestMemoryConnector:
    """Test cases for MemoryConnector."""
    
    @pytest.fixture
    def connector(self):
        return MemoryConnector(TestDataModel)
    
    @pytest.mark.asyncio
    async def test_connect_disconnect(self, connector):
        """Test connection lifecycle."""
        await connector.connect()
        assert connector._connected
        
        await connector.disconnect()
        assert not connector._connected
    
    @pytest.mark.asyncio
    async def test_provide_empty(self, connector):
        """Test providing data when storage is empty."""
        await connector.connect()
        data = await connector.provide()
        assert isinstance(data, TestDataModel)
        assert data.name == "test"
        assert data.value == 42
    
    @pytest.mark.asyncio
    async def test_consume_and_provide(self, connector):
        """Test consuming and then providing data."""
        await connector.connect()
        
        # Create test data
        test_data = TestDataModel(name="custom", value=100, timestamp="2024-01-02T00:00:00Z")
        
        # Consume data
        await connector.consume(test_data)
        
        # Provide data back
        retrieved_data = await connector.provide()
        assert retrieved_data.name == "custom"
        assert retrieved_data.value == 100
        assert retrieved_data.timestamp == "2024-01-02T00:00:00Z"
    
    @pytest.mark.asyncio
    async def test_consume_with_meta(self, connector):
        """Test consuming data with metadata."""
        await connector.connect()
        
        test_data = TestDataModel(name="with_meta", value=200)
        meta = {"source": "test", "priority": "high"}
        
        await connector.consume(test_data, meta=meta)
        
        # Check that metadata was stored
        assert connector._meta == meta
    
    @pytest.mark.asyncio
    async def test_receive_streaming(self, connector):
        """Test receiving data as a stream."""
        await connector.connect()
        
        # Add some data
        test_data1 = TestDataModel(name="first", value=1)
        test_data2 = TestDataModel(name="second", value=2)
        
        await connector.consume(test_data1)
        await connector.consume(test_data2)
        
        # Test receive
        received = []
        async for data in connector.receive():
            received.append(data)
            if len(received) >= 2:
                break
        
        assert len(received) == 2
        assert received[0].name == "first"
        assert received[1].name == "second"
    
    @pytest.mark.asyncio
    async def test_subscribe_unsubscribe(self, connector):
        """Test subscription mechanism."""
        await connector.connect()
        
        # Subscribe
        queue = await connector.subscribe()
        assert queue in connector._subscribers
        
        # Unsubscribe
        await connector.unsubscribe(queue)
        assert queue not in connector._subscribers
    
    @pytest.mark.asyncio
    async def test_clear_storage(self, connector):
        """Test clearing storage."""
        await connector.connect()
        
        # Add some data
        test_data = TestDataModel(name="to_clear", value=999)
        await connector.consume(test_data)
        
        # Clear
        await connector.clear()
        
        # Verify data is cleared
        retrieved = await connector.provide()
        assert retrieved.name == "test"  # Default values
        assert retrieved.value == 42


class TestHttpInConnector:
    """Test cases for HttpInConnector."""
    
    @pytest.fixture
    def config(self):
        return HttpConnectorConfig(
            base_url="http://localhost:8000/api",
            timeout=5.0
        )
    
    @pytest.fixture
    def connector(self, config):
        return HttpInConnector(config, TestDataModel)
    
    @pytest.mark.asyncio
    async def test_connect_disconnect(self, connector):
        """Test connection lifecycle."""
        with patch('aiohttp.ClientSession') as mock_session:
            mock_session.return_value = AsyncMock()
            
            await connector.connect()
            assert connector._session is not None
            assert connector._running
            
            await connector.disconnect()
            assert not connector._running
            assert connector._session is None
    
    @pytest.mark.asyncio
    async def test_provide_success(self, connector):
        """Test successful data provision."""
        await connector.connect()
        
        # Mock response
        mock_response = AsyncMock()
        mock_response.json.return_value = {"name": "http_data", "value": 123, "timestamp": "2024-01-01T00:00:00Z"}
        mock_response.__aenter__.return_value = mock_response
        mock_response.__aexit__.return_value = None
        
        connector._session.get.return_value = mock_response
        
        data = await connector.provide()
        assert data.name == "http_data"
        assert data.value == 123
    
    @pytest.mark.asyncio
    async def test_provide_connection_error(self, connector):
        """Test provision with connection error."""
        await connector.connect()
        
        connector._session.get.side_effect = Exception("Connection failed")
        
        with pytest.raises(ConnectionError):
            await connector.provide()
    
    @pytest.mark.asyncio
    async def test_consume_success(self, connector):
        """Test successful data consumption."""
        await connector.connect()
        
        # Mock response
        mock_response = AsyncMock()
        mock_response.__aenter__.return_value = mock_response
        mock_response.__aexit__.return_value = None
        
        connector._session.post.return_value = mock_response
        
        test_data = TestDataModel(name="to_send", value=456)
        await connector.consume(test_data)
        
        # Verify POST was called
        connector._session.post.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_consume_with_meta(self, connector):
        """Test consuming data with metadata."""
        await connector.connect()
        
        mock_response = AsyncMock()
        mock_response.__aenter__.return_value = mock_response
        mock_response.__aexit__.return_value = None
        
        connector._session.post.return_value = mock_response
        
        test_data = TestDataModel(name="with_meta", value=789)
        meta = {"source": "test", "priority": "high"}
        
        await connector.consume(test_data, meta=meta)
        
        # Verify metadata was included in payload
        call_args = connector._session.post.call_args
        payload = call_args[1]['json']
        assert payload["_meta"] == meta


class TestHttpOutConnector:
    """Test cases for HttpOutConnector."""
    
    @pytest.fixture
    def config(self):
        return HttpConnectorConfig(
            base_url="http://localhost:8000/api",
            timeout=5.0
        )
    
    @pytest.fixture
    def connector(self, config):
        return HttpOutConnector(config, TestDataModel)
    
    @pytest.mark.asyncio
    async def test_connect_disconnect(self, connector):
        """Test connection lifecycle."""
        with patch('httpx.AsyncClient') as mock_client:
            mock_client.return_value = AsyncMock()
            
            await connector.connect()
            assert connector._session is not None
            
            await connector.disconnect()
            assert connector._session is None
    
    @pytest.mark.asyncio
    async def test_provide_success(self, connector):
        """Test successful data provision."""
        await connector.connect()
        
        # Mock response
        mock_response = AsyncMock()
        mock_response.json.return_value = {"name": "http_data", "value": 123, "timestamp": "2024-01-01T00:00:00Z"}
        
        connector._session.get.return_value = mock_response
        
        data = await connector.provide()
        assert data.name == "http_data"
        assert data.value == 123
    
    @pytest.mark.asyncio
    async def test_consume_success(self, connector):
        """Test successful data consumption."""
        await connector.connect()
        
        # Mock response
        mock_response = AsyncMock()
        connector._session.post.return_value = mock_response
        
        test_data = TestDataModel(name="to_send", value=456)
        await connector.consume(test_data)
        
        # Verify POST was called
        connector._session.post.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_connect_with_auth(self, connector):
        """Test connection with authentication."""
        connector.config.auth = {"username": "user", "password": "pass"}
        
        with patch('httpx.AsyncClient') as mock_client:
            mock_client.return_value = AsyncMock()
            
            await connector.connect()
            
            # Verify auth was set
            connector._session.auth = ("user", "pass")


class TestSqlConnector:
    """Test cases for SqlConnector."""
    
    @pytest.fixture
    def config(self):
        return SqlConnectorConfig(
            host="localhost",
            port=5432,
            database="testdb",
            username="testuser",
            password="testpass",
            table_name="test_table"
        )
    
    @pytest.fixture
    def connector(self, config):
        return SqlConnector(config, TestDataModel)
    
    @pytest.mark.asyncio
    async def test_connect_disconnect(self, connector):
        """Test connection lifecycle."""
        with patch('asyncpg.create_pool') as mock_create_pool:
            mock_pool = AsyncMock()
            mock_create_pool.return_value = mock_pool
            
            await connector.connect()
            assert connector._pool is not None
            
            await connector.disconnect()
            assert connector._pool is None
    
    @pytest.mark.asyncio
    async def test_provide_with_data(self, connector):
        """Test providing data when table has data."""
        await connector.connect()
        
        # Mock pool and connection
        mock_conn = AsyncMock()
        mock_pool = AsyncMock()
        mock_pool.acquire.return_value.__aenter__.return_value = mock_conn
        mock_pool.acquire.return_value.__aexit__.return_value = None
        
        connector._pool = mock_pool
        
        # Mock query result
        mock_row = {"data": '{"name": "db_data", "value": 999, "timestamp": "2024-01-01T00:00:00Z"}'}
        mock_conn.fetchrow.return_value = mock_row
        
        data = await connector.provide()
        assert data.name == "db_data"
        assert data.value == 999
    
    @pytest.mark.asyncio
    async def test_provide_empty_table(self, connector):
        """Test providing data when table is empty."""
        await connector.connect()
        
        mock_conn = AsyncMock()
        mock_pool = AsyncMock()
        mock_pool.acquire.return_value.__aenter__.return_value = mock_conn
        mock_pool.acquire.return_value.__aexit__.return_value = None
        
        connector._pool = mock_pool
        
        # Mock empty result
        mock_conn.fetchrow.return_value = None
        
        data = await connector.provide()
        assert isinstance(data, TestDataModel)
        assert data.name == "test"  # Default values
    
    @pytest.mark.asyncio
    async def test_consume_success(self, connector):
        """Test successful data consumption."""
        await connector.connect()
        
        mock_conn = AsyncMock()
        mock_pool = AsyncMock()
        mock_pool.acquire.return_value.__aenter__.return_value = mock_conn
        mock_pool.acquire.return_value.__aexit__.return_value = None
        
        connector._pool = mock_pool
        
        test_data = TestDataModel(name="to_store", value=777)
        await connector.consume(test_data)
        
        # Verify INSERT was executed
        mock_conn.execute.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_ensure_table_exists(self, connector):
        """Test table creation logic."""
        await connector.connect()
        
        mock_conn = AsyncMock()
        mock_pool = AsyncMock()
        mock_pool.acquire.return_value.__aenter__.return_value = mock_conn
        mock_pool.acquire.return_value.__aexit__.return_value = None
        
        connector._pool = mock_pool
        
        # Mock table doesn't exist
        mock_conn.fetchval.return_value = False
        
        await connector._ensure_table_exists()
        
        # Verify CREATE TABLE was executed
        assert mock_conn.execute.call_count >= 1


class TestRedisConnector:
    """Test cases for RedisConnector."""
    
    @pytest.fixture
    def config(self):
        return RedisConnectorConfig(
            host="localhost",
            port=6379,
            database=0,
            key_prefix="test:"
        )
    
    @pytest.fixture
    def connector(self, config):
        return RedisConnector(config, TestDataModel)
    
    @pytest.mark.asyncio
    async def test_connect_disconnect(self, connector):
        """Test connection lifecycle."""
        with patch('aioredis.from_url') as mock_from_url:
            mock_redis = AsyncMock()
            mock_from_url.return_value = mock_redis
            
            await connector.connect()
            assert connector._redis is not None
            assert connector._running
            
            await connector.disconnect()
            assert not connector._running
            assert connector._redis is None
    
    @pytest.mark.asyncio
    async def test_provide_with_data(self, connector):
        """Test providing data when Redis has data."""
        await connector.connect()
        
        # Mock Redis operations
        mock_redis = AsyncMock()
        mock_redis.zrevrange.return_value = [("test:data:123", 123.0)]
        mock_redis.get.return_value = '{"name": "redis_data", "value": 555, "timestamp": "2024-01-01T00:00:00Z"}'
        
        connector._redis = mock_redis
        
        data = await connector.provide()
        assert data.name == "redis_data"
        assert data.value == 555
    
    @pytest.mark.asyncio
    async def test_provide_empty_redis(self, connector):
        """Test providing data when Redis is empty."""
        await connector.connect()
        
        mock_redis = AsyncMock()
        mock_redis.zrevrange.return_value = []
        
        connector._redis = mock_redis
        
        data = await connector.provide()
        assert isinstance(data, TestDataModel)
        assert data.name == "test"  # Default values
    
    @pytest.mark.asyncio
    async def test_consume_success(self, connector):
        """Test successful data consumption."""
        await connector.connect()
        
        mock_redis = AsyncMock()
        connector._redis = mock_redis
        
        test_data = TestDataModel(name="to_store", value=888)
        await connector.consume(test_data)
        
        # Verify Redis operations were called
        mock_redis.set.assert_called_once()
        mock_redis.zadd.assert_called_once()
        mock_redis.publish.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_get_by_key(self, connector):
        """Test getting data by specific key."""
        await connector.connect()
        
        mock_redis = AsyncMock()
        mock_redis.get.return_value = '{"name": "key_data", "value": 111, "timestamp": "2024-01-01T00:00:00Z"}'
        
        connector._redis = mock_redis
        
        data = await connector.get_by_key("test:key:123")
        assert data.name == "key_data"
        assert data.value == 111
    
    @pytest.mark.asyncio
    async def test_set_by_key(self, connector):
        """Test setting data by specific key."""
        await connector.connect()
        
        mock_redis = AsyncMock()
        connector._redis = mock_redis
        
        test_data = TestDataModel(name="key_value", value=222)
        await connector.set_by_key("test:key:456", test_data)
        
        # Verify Redis operations
        mock_redis.set.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_count_records(self, connector):
        """Test counting total records."""
        await connector.connect()
        
        mock_redis = AsyncMock()
        mock_redis.zcard.return_value = 5
        
        connector._redis = mock_redis
        
        count = await connector.count()
        assert count == 5
    
    @pytest.mark.asyncio
    async def test_clear_all_data(self, connector):
        """Test clearing all data."""
        await connector.connect()
        
        mock_redis = AsyncMock()
        mock_redis.keys.return_value = ["test:key1", "test:key2"]
        
        connector._redis = mock_redis
        
        await connector.clear()
        
        # Verify delete was called
        mock_redis.delete.assert_called_once_with("test:key1", "test:key2")


# Integration test helpers
class TestConnectorIntegration:
    """Integration tests for connectors working together."""
    
    @pytest.mark.asyncio
    async def test_memory_to_http_flow(self):
        """Test data flow from memory connector to HTTP connector."""
        # Create connectors
        memory_connector = MemoryConnector(TestDataModel)
        http_config = HttpConnectorConfig(base_url="http://localhost:8000/api")
        http_connector = HttpOutConnector(http_config, TestDataModel)
        
        # Connect both
        await memory_connector.connect()
        await http_connector.connect()
        
        # Store data in memory
        test_data = TestDataModel(name="integration_test", value=999)
        await memory_connector.consume(test_data)
        
        # Retrieve from memory
        retrieved_data = await memory_connector.provide()
        assert retrieved_data.name == "integration_test"
        
        # Send to HTTP (mocked)
        with patch.object(http_connector._session, 'post') as mock_post:
            mock_response = AsyncMock()
            mock_post.return_value = mock_response
            
            await http_connector.consume(retrieved_data)
            mock_post.assert_called_once()
        
        # Cleanup
        await memory_connector.disconnect()
        await http_connector.disconnect()
    
    @pytest.mark.asyncio
    async def test_connector_error_handling(self):
        """Test that connectors properly handle errors."""
        # Test memory connector with invalid data
        memory_connector = MemoryConnector(TestDataModel)
        await memory_connector.connect()
        
        # This should work fine
        test_data = TestDataModel(name="valid", value=123)
        await memory_connector.consume(test_data)
        
        # Test HTTP connector with connection failure
        http_config = HttpConnectorConfig(base_url="http://invalid-host:9999")
        http_connector = HttpOutConnector(http_config, TestDataModel)
        
        # Should raise connection error
        with pytest.raises(ConnectionError):
            await http_connector.connect()
        
        await memory_connector.disconnect()


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
