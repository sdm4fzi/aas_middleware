import pytest
import asyncio
import json
import httpx
import time
from typing import Dict, Any, List
from unittest.mock import AsyncMock, patch

from aas_middleware.facade.builder import AppBuilder
from aas_middleware.facade.rest_api import MiddlewareRestAPI
from aas_middleware.domain.data_model import DataModel
from aas_middleware.adapters.connectors import (
    MemoryConnector, HttpConnectorConfig, SqlConnectorConfig, RedisConnectorConfig
)


# Test data model
class TestDataModel(DataModel):
    name: str = "test"
    value: int = 42
    timestamp: str = "2024-01-01T00:00:00Z"


class TestIntegrationConnectors:
    """Integration tests for connectors via REST API."""
    
    @pytest.fixture
    async def app(self):
        """Create and configure the middleware application."""
        builder = AppBuilder()
        app = builder.meta(
            name="test_app",
            version="1.0.0",
            description="Test application for integration testing"
        ).models([
            TestDataModel
        ]).connector(
            "memory_test",
            MemoryConnector,
            TestDataModel
        ).connector(
            "http_in_test",
            "HttpInConnector",
            TestDataModel,
            config=HttpConnectorConfig(
                base_url="http://localhost:8001/api",
                timeout=5.0
            )
        ).connector(
            "http_out_test",
            "HttpOutConnector", 
            TestDataModel,
            config=HttpConnectorConfig(
                base_url="http://localhost:8002/api",
                timeout=5.0
            )
        ).build()
        
        # Start the app
        await app.start()
        yield app
        
        # Cleanup
        await app.stop()
    
    @pytest.fixture
    async def rest_api(self, app):
        """Create the REST API middleware."""
        api = MiddlewareRestAPI(app)
        return api
    
    @pytest.fixture
    async def client(self, rest_api):
        """Create an async HTTP client for testing."""
        async with httpx.AsyncClient(app=rest_api.get_app(), base_url="http://test") as client:
            yield client
    
    @pytest.mark.asyncio
    async def test_health_endpoint(self, client):
        """Test the health check endpoint."""
        response = await client.get("/health")
        assert response.status_code == 200
        
        data = response.json()
        assert "status" in data
        assert "running" in data
        assert "timestamp" in data
    
    @pytest.mark.asyncio
    async def test_list_connectors(self, client):
        """Test listing all connectors."""
        response = await client.get("/connectors")
        assert response.status_code == 200
        
        data = response.json()
        assert "connectors" in data
        assert len(data["connectors"]) >= 3  # memory, http_in, http_out
        
        # Check connector types
        connector_types = [c["type"] for c in data["connectors"]]
        assert "MemoryConnector" in connector_types
        assert "HttpInConnector" in connector_types
        assert "HttpOutConnector" in connector_types
    
    @pytest.mark.asyncio
    async def test_connector_status(self, client):
        """Test getting individual connector status."""
        response = await client.get("/connectors/memory_test")
        assert response.status_code == 200
        
        data = response.json()
        assert data["connector_id"] == "memory_test"
        assert data["type"] == "MemoryConnector"
        assert data["data_model"] == "TestDataModel"
        assert "config" in data
    
    @pytest.mark.asyncio
    async def test_connector_not_found(self, client):
        """Test getting status of non-existent connector."""
        response = await client.get("/connectors/nonexistent")
        assert response.status_code == 404
        
        data = response.json()
        assert "detail" in data
        assert "not found" in data["detail"]
    
    @pytest.mark.asyncio
    async def test_memory_connector_operations(self, client):
        """Test complete memory connector operations via REST API."""
        # Test consuming data
        test_data = {
            "name": "integration_test",
            "value": 999,
            "timestamp": "2024-01-02T00:00:00Z"
        }
        
        consume_response = await client.post(
            "/connectors/memory_test/consume",
            json={
                "connector_id": "memory_test",
                "data": test_data,
                "meta": {"source": "integration_test"}
            }
        )
        assert consume_response.status_code == 200
        
        data = consume_response.json()
        assert data["success"] is True
        assert "consumed successfully" in data["message"]
        
        # Test providing data
        provide_response = await client.get("/connectors/memory_test/provide")
        assert provide_response.status_code == 200
        
        data = provide_response.json()
        assert data["success"] is True
        assert data["data"] is not None
        assert data["data"]["name"] == "integration_test"
        assert data["data"]["value"] == 999
        
        # Test receiving data stream
        receive_response = await client.get("/connectors/memory_test/receive?limit=5")
        assert receive_response.status_code == 200
        
        data = receive_response.json()
        assert data["success"] is True
        assert "items" in data["data"]
        assert data["data"]["count"] >= 1
        
        # Test counting data
        count_response = await client.get("/connectors/memory_test/count")
        assert count_response.status_code == 200
        
        data = count_response.json()
        assert "count" in data
        assert data["count"] >= 1
        
        # Test clearing data
        clear_response = await client.post("/connectors/memory_test/clear")
        assert clear_response.status_code == 200
        
        data = clear_response.json()
        assert "cleared successfully" in data["message"]
        
        # Verify data was cleared
        count_response = await client.get("/connectors/memory_test/count")
        data = count_response.json()
        assert data["count"] == 0
    
    @pytest.mark.asyncio
    async def test_http_connector_operations(self, client):
        """Test HTTP connector operations via REST API."""
        # Test connecting HTTP connector
        connect_response = await client.post("/connectors/http_in_test/connect")
        assert connect_response.status_code == 200
        
        data = connect_response.json()
        assert "connected successfully" in data["message"]
        
        # Test disconnecting HTTP connector
        disconnect_response = await client.post("/connectors/http_in_test/disconnect")
        assert disconnect_response.status_code == 200
        
        data = disconnect_response.json()
        assert "disconnected successfully" in data["message"]
    
    @pytest.mark.asyncio
    async def test_connector_connection_lifecycle(self, client):
        """Test connector connection lifecycle management."""
        # Test connecting memory connector
        connect_response = await client.post("/connectors/memory_test/connect")
        assert connect_response.status_code == 200
        
        # Check status shows connected
        status_response = await client.get("/connectors/memory_test")
        assert status_response.status_code == 200
        
        data = status_response.json()
        assert data["connected"] is True
        
        # Test disconnecting
        disconnect_response = await client.post("/connectors/memory_test/disconnect")
        assert disconnect_response.status_code == 200
        
        # Check status shows disconnected
        status_response = await client.get("/connectors/memory_test")
        data = status_response.json()
        assert data["connected"] is False
    
    @pytest.mark.asyncio
    async def test_data_flow_between_connectors(self, client):
        """Test data flow between different connectors."""
        # Store data in memory connector
        test_data = {
            "name": "flow_test",
            "value": 123,
            "timestamp": "2024-01-03T00:00:00Z"
        }
        
        await client.post(
            "/connectors/memory_test/consume",
            json={
                "connector_id": "memory_test",
                "data": test_data
            }
        )
        
        # Retrieve from memory connector
        provide_response = await client.get("/connectors/memory_test/provide")
        data = provide_response.json()
        assert data["success"] is True
        assert data["data"]["name"] == "flow_test"
        
        # Store in another connector (simulating data flow)
        await client.post(
            "/connectors/memory_test/consume",
            json={
                "connector_id": "memory_test",
                "data": {
                    "name": "flow_test_2",
                    "value": 456,
                    "timestamp": "2024-01-03T01:00:00Z"
                }
            }
        )
        
        # Verify both data items exist
        count_response = await client.get("/connectors/memory_test/count")
        data = count_response.json()
        assert data["count"] == 2
    
    @pytest.mark.asyncio
    async def test_error_handling(self, client):
        """Test error handling in the REST API."""
        # Test invalid connector ID
        response = await client.get("/connectors/invalid_id/provide")
        assert response.status_code == 404
        
        # Test invalid data for consumption
        response = await client.post(
            "/connectors/memory_test/consume",
            json={
                "connector_id": "memory_test",
                "data": None  # Invalid: data is required
            }
        )
        assert response.status_code == 400
        
        data = response.json()
        assert "detail" in data
        assert "required" in data["detail"]
    
    @pytest.mark.asyncio
    async def test_workflow_endpoints(self, client):
        """Test workflow-related endpoints."""
        # Test listing workflows
        response = await client.get("/workflows")
        assert response.status_code == 200
        
        data = response.json()
        assert "workflows" in data
    
    @pytest.mark.asyncio
    async def test_binding_endpoints(self, client):
        """Test binding-related endpoints."""
        # Test listing bindings
        response = await client.get("/bindings")
        assert response.status_code == 200
        
        data = response.json()
        assert "bindings" in data
    
    @pytest.mark.asyncio
    async def test_concurrent_operations(self, client):
        """Test concurrent operations on connectors."""
        # Create multiple concurrent requests
        async def consume_data(i: int):
            return await client.post(
                "/connectors/memory_test/consume",
                json={
                    "connector_id": "memory_test",
                    "data": {
                        "name": f"concurrent_{i}",
                        "value": i,
                        "timestamp": f"2024-01-04T{i:02d}:00:00Z"
                    }
                }
            )
        
        # Execute concurrent operations
        tasks = [consume_data(i) for i in range(5)]
        responses = await asyncio.gather(*tasks)
        
        # Verify all operations succeeded
        for response in responses:
            assert response.status_code == 200
        
        # Verify data count
        count_response = await client.get("/connectors/memory_test/count")
        data = count_response.json()
        assert data["count"] == 5
    
    @pytest.mark.asyncio
    async def test_metadata_handling(self, client):
        """Test metadata handling in connector operations."""
        test_data = {
            "name": "metadata_test",
            "value": 777,
            "timestamp": "2024-01-05T00:00:00Z"
        }
        
        meta = {
            "source": "integration_test",
            "priority": "high",
            "tags": ["test", "metadata"],
            "timestamp": "2024-01-05T00:00:00Z"
        }
        
        # Consume with metadata
        response = await client.post(
            "/connectors/memory_test/consume",
            json={
                "connector_id": "memory_test",
                "data": test_data,
                "meta": meta
            }
        )
        assert response.status_code == 200
        
        # Verify data was stored with metadata
        provide_response = await client.get("/connectors/memory_test/provide")
        data = provide_response.json()
        assert data["success"] is True
        assert data["data"]["name"] == "metadata_test"
    
    @pytest.mark.asyncio
    async def test_streaming_receive(self, client):
        """Test streaming data reception."""
        # Add multiple data items
        for i in range(3):
            await client.post(
                "/connectors/memory_test/consume",
                json={
                    "connector_id": "memory_test",
                    "data": {
                        "name": f"stream_{i}",
                        "value": i * 100,
                        "timestamp": f"2024-01-06T{i:02d}:00:00Z"
                    }
                }
            )
        
        # Test streaming with different limits
        for limit in [1, 2, 3]:
            response = await client.get(f"/connectors/memory_test/receive?limit={limit}")
            assert response.status_code == 200
            
            data = response.json()
            assert data["success"] is True
            assert data["data"]["count"] == min(limit, 3)
    
    @pytest.mark.asyncio
    async def test_connector_configuration(self, client):
        """Test connector configuration retrieval."""
        # Test HTTP connector configuration
        response = await client.get("/connectors/http_in_test")
        assert response.status_code == 200
        
        data = response.json()
        assert "config" in data
        config = data["config"]
        
        # Verify configuration fields
        assert "base_url" in config
        assert "timeout" in config
        assert config["base_url"] == "http://localhost:8001/api"
        assert config["timeout"] == 5.0


class TestIntegrationWithRealConnectors:
    """Integration tests with real connector implementations."""
    
    @pytest.fixture
    async def real_app(self):
        """Create app with real connector implementations."""
        builder = AppBuilder()
        app = builder.meta(
            name="real_test_app",
            version="1.0.0"
        ).models([
            TestDataModel
        ]).connector(
            "real_memory",
            MemoryConnector,
            TestDataModel
        ).build()
        
        await app.start()
        yield app
        await app.stop()
    
    @pytest.mark.asyncio
    async def test_real_memory_connector_operations(self, real_app):
        """Test real memory connector operations."""
        # Get connector from registry
        connector = real_app.connector_registry.get("real_memory")
        assert connector is not None
        assert isinstance(connector, MemoryConnector)
        
        # Test direct connector operations
        await connector.connect()
        assert connector._connected
        
        # Test data operations
        test_data = TestDataModel(name="real_test", value=888)
        await connector.consume(test_data)
        
        retrieved = await connector.provide()
        assert retrieved.name == "real_test"
        assert retrieved.value == 888
        
        await connector.disconnect()
        assert not connector._connected
    
    @pytest.mark.asyncio
    async def test_connector_registry_integration(self, real_app):
        """Test connector registry integration."""
        registry = real_app.connector_registry
        
        # Verify connector is registered
        assert "real_memory" in registry.list()
        assert registry.count() >= 1
        
        # Test connector retrieval
        connector = registry.get("real_memory")
        assert connector is not None
        
        # Test connector removal
        registry.remove("real_memory")
        assert "real_memory" not in registry.list()
        assert registry.get("real_memory") is None


class TestPerformanceAndStress:
    """Performance and stress tests for the integration."""
    
    @pytest.mark.asyncio
    async def test_bulk_data_operations(self, client):
        """Test bulk data operations performance."""
        # Measure time for bulk insert
        start_time = time.time()
        
        # Insert 100 data items
        for i in range(100):
            await client.post(
                "/connectors/memory_test/consume",
                json={
                    "connector_id": "memory_test",
                    "data": {
                        "name": f"bulk_{i}",
                        "value": i,
                        "timestamp": f"2024-01-07T{i:02d}:00:00Z"
                    }
                }
            )
        
        insert_time = time.time() - start_time
        print(f"Bulk insert of 100 items took: {insert_time:.2f} seconds")
        
        # Verify count
        count_response = await client.get("/connectors/memory_test/count")
        data = count_response.json()
        assert data["count"] == 100
        
        # Measure time for bulk retrieval
        start_time = time.time()
        receive_response = await client.get("/connectors/memory_test/receive?limit=100")
        retrieve_time = time.time() - start_time
        print(f"Bulk retrieval of 100 items took: {retrieve_time:.2f} seconds")
        
        assert receive_response.status_code == 200
        data = receive_response.json()
        assert data["data"]["count"] == 100
        
        # Cleanup
        await client.post("/connectors/memory_test/clear")
    
    @pytest.mark.asyncio
    async def test_concurrent_user_simulation(self, client):
        """Simulate multiple concurrent users."""
        async def user_workflow(user_id: int):
            """Simulate a user workflow."""
            # Consume data
            await client.post(
                "/connectors/memory_test/consume",
                json={
                    "connector_id": "memory_test",
                    "data": {
                        "name": f"user_{user_id}",
                        "value": user_id * 1000,
                        "timestamp": f"2024-01-08T{user_id:02d}:00:00Z"
                    }
                }
            )
            
            # Provide data
            await client.get("/connectors/memory_test/provide")
            
            # Get count
            await client.get("/connectors/memory_test/count")
        
        # Simulate 10 concurrent users
        start_time = time.time()
        tasks = [user_workflow(i) for i in range(10)]
        await asyncio.gather(*tasks)
        total_time = time.time() - start_time
        
        print(f"10 concurrent users completed in: {total_time:.2f} seconds")
        
        # Verify data integrity
        count_response = await client.get("/connectors/memory_test/count")
        data = count_response.json()
        assert data["count"] == 10
        
        # Cleanup
        await client.post("/connectors/memory_test/clear")


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
