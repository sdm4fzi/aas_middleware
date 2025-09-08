#!/usr/bin/env python3
"""
Comprehensive example demonstrating all connector types working together.
This example shows how to use Memory, HTTP, SQL, and Redis connectors
in a single middleware application.
"""

import asyncio
import json
import logging
from datetime import datetime
from typing import Dict, Any

from aas_middleware.facade.builder import AppBuilder
from aas_middleware.facade.rest_api import MiddlewareRestAPI
from aas_middleware.domain.data_model import DataModel
from aas_middleware.adapters.connectors import (
    MemoryConnector, HttpConnectorConfig, SqlConnectorConfig, RedisConnectorConfig
)

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


# Define a comprehensive data model
class SensorData(DataModel):
    """Sensor data model for demonstration."""
    sensor_id: str = "unknown"
    temperature: float = 0.0
    humidity: float = 0.0
    pressure: float = 0.0
    timestamp: str = "2024-01-01T00:00:00Z"
    location: str = "unknown"
    status: str = "active"


class DeviceStatus(DataModel):
    """Device status model for demonstration."""
    device_id: str = "unknown"
    status: str = "offline"
    last_seen: str = "2024-01-01T00:00:00Z"
    battery_level: float = 0.0
    firmware_version: str = "1.0.0"
    location: str = "unknown"


async def demonstrate_memory_connector(app):
    """Demonstrate memory connector operations."""
    logger.info("=== Demonstrating Memory Connector ===")
    
    # Get the memory connector
    memory_connector = app.connector_registry.get("memory_sensor")
    
    # Store some sensor data
    sensor_data = SensorData(
        sensor_id="SENSOR_001",
        temperature=23.5,
        humidity=45.2,
        pressure=1013.25,
        timestamp=datetime.utcnow().isoformat(),
        location="Building A, Floor 1"
    )
    
    await memory_connector.consume(sensor_data, meta={"source": "demo", "priority": "high"})
    logger.info(f"Stored sensor data: {sensor_data.sensor_id}")
    
    # Retrieve the data
    retrieved_data = await memory_connector.provide()
    logger.info(f"Retrieved sensor data: {retrieved_data.sensor_id}, Temp: {retrieved_data.temperature}°C")
    
    # Store more data for streaming demonstration
    for i in range(3):
        data = SensorData(
            sensor_id=f"SENSOR_{i+2:03d}",
            temperature=20.0 + i * 2.0,
            humidity=40.0 + i * 5.0,
            pressure=1010.0 + i * 2.0,
            timestamp=datetime.utcnow().isoformat(),
            location=f"Building {chr(65+i)}, Floor {i+1}"
        )
        await memory_connector.consume(data)
    
    # Demonstrate streaming
    logger.info("Streaming data from memory connector:")
    count = 0
    async for data in memory_connector.receive():
        logger.info(f"  Streamed: {data.sensor_id} - {data.temperature}°C")
        count += 1
        if count >= 3:
            break
    
    # Get count
    count = await memory_connector.count()
    logger.info(f"Total items in memory connector: {count}")


async def demonstrate_http_connectors(app):
    """Demonstrate HTTP connector operations."""
    logger.info("=== Demonstrating HTTP Connectors ===")
    
    # Get HTTP connectors
    http_in = app.connector_registry.get("http_in")
    http_out = app.connector_registry.get("http_out")
    
    # Connect HTTP connectors
    await http_in.connect()
    await http_out.connect()
    logger.info("HTTP connectors connected")
    
    # Create test data
    device_status = DeviceStatus(
        device_id="DEVICE_001",
        status="online",
        last_seen=datetime.utcnow().isoformat(),
        battery_level=85.5,
        firmware_version="2.1.0",
        location="Server Room A"
    )
    
    # Send data via HTTP out connector
    try:
        await http_out.consume(device_status, meta={"destination": "external_api"})
        logger.info(f"Sent device status via HTTP: {device_status.device_id}")
    except Exception as e:
        logger.warning(f"HTTP out failed (expected in demo): {e}")
    
    # Try to receive data via HTTP in connector
    try:
        data = await http_in.provide()
        logger.info(f"Received data via HTTP: {data}")
    except Exception as e:
        logger.warning(f"HTTP in failed (expected in demo): {e}")
    
    # Disconnect
    await http_in.disconnect()
    await http_out.disconnect()
    logger.info("HTTP connectors disconnected")


async def demonstrate_sql_connector(app):
    """Demonstrate SQL connector operations."""
    logger.info("=== Demonstrating SQL Connector ===")
    
    # Get the SQL connector
    sql_connector = app.connector_registry.get("sql_sensor")
    
    # Try to connect (will fail without real database, but shows the flow)
    try:
        await sql_connector.connect()
        logger.info("SQL connector connected")
        
        # Store some data
        sensor_data = SensorData(
            sensor_id="DB_SENSOR_001",
            temperature=25.0,
            humidity=50.0,
            pressure=1015.0,
            timestamp=datetime.utcnow().isoformat(),
            location="Database Demo"
        )
        
        await sql_connector.consume(sensor_data)
        logger.info(f"Stored sensor data in SQL: {sensor_data.sensor_id}")
        
        # Try to retrieve
        retrieved = await sql_connector.provide()
        logger.info(f"Retrieved from SQL: {retrieved.sensor_id}")
        
    except Exception as e:
        logger.warning(f"SQL connector demo failed (expected without real DB): {e}")
    
    finally:
        try:
            await sql_connector.disconnect()
            logger.info("SQL connector disconnected")
        except:
            pass


async def demonstrate_redis_connector(app):
    """Demonstrate Redis connector operations."""
    logger.info("=== Demonstrating Redis Connector ===")
    
    # Get the Redis connector
    redis_connector = app.connector_registry.get("redis_sensor")
    
    # Try to connect (will fail without real Redis, but shows the flow)
    try:
        await redis_connector.connect()
        logger.info("Redis connector connected")
        
        # Store some data
        sensor_data = SensorData(
            sensor_id="REDIS_SENSOR_001",
            temperature=22.0,
            humidity=48.0,
            pressure=1012.0,
            timestamp=datetime.utcnow().isoformat(),
            location="Redis Demo"
        )
        
        await redis_connector.consume(sensor_data)
        logger.info(f"Stored sensor data in Redis: {sensor_data.sensor_id}")
        
        # Try to retrieve
        retrieved = await redis_connector.provide()
        logger.info(f"Retrieved from Redis: {retrieved.sensor_id}")
        
        # Test key-based operations
        await redis_connector.set_by_key("custom_key", sensor_data)
        custom_data = await redis_connector.get_by_key("custom_key")
        logger.info(f"Custom key data: {custom_data.sensor_id}")
        
    except Exception as e:
        logger.warning(f"Redis connector demo failed (expected without real Redis): {e}")
    
    finally:
        try:
            await redis_connector.disconnect()
            logger.info("Redis connector disconnected")
        except:
            pass


async def demonstrate_rest_api(app):
    """Demonstrate the REST API functionality."""
    logger.info("=== Demonstrating REST API ===")
    
    # Create REST API
    rest_api = MiddlewareRestAPI(app)
    
    # Get the FastAPI app
    fastapi_app = rest_api.get_app()
    
    # Test some endpoints programmatically
    from fastapi.testclient import TestClient
    
    client = TestClient(fastapi_app)
    
    # Test health endpoint
    response = client.get("/health")
    logger.info(f"Health endpoint: {response.status_code}")
    
    # Test connectors endpoint
    response = client.get("/connectors")
    logger.info(f"Connectors endpoint: {response.status_code}")
    if response.status_code == 200:
        connectors = response.json()
        logger.info(f"Found {len(connectors['connectors'])} connectors")
    
    # Test memory connector operations via REST API
    test_data = {
        "sensor_id": "REST_API_SENSOR",
        "temperature": 24.0,
        "humidity": 52.0,
        "pressure": 1014.0,
        "timestamp": datetime.utcnow().isoformat(),
        "location": "REST API Demo"
    }
    
    # Consume data via REST API
    response = client.post(
        "/connectors/memory_sensor/consume",
        json={
            "connector_id": "memory_sensor",
            "data": test_data,
            "meta": {"source": "rest_api_demo"}
        }
    )
    logger.info(f"REST API consume: {response.status_code}")
    
    # Provide data via REST API
    response = client.get("/connectors/memory_sensor/provide")
    logger.info(f"REST API provide: {response.status_code}")
    if response.status_code == 200:
        data = response.json()
        logger.info(f"Retrieved via REST API: {data['data']['sensor_id']}")


async def demonstrate_data_flow(app):
    """Demonstrate data flow between different connectors."""
    logger.info("=== Demonstrating Data Flow ===")
    
    # Create a workflow: Memory -> Process -> Memory
    memory_source = app.connector_registry.get("memory_sensor")
    memory_dest = app.connector_registry.get("memory_device")
    
    # Generate source data
    source_data = SensorData(
        sensor_id="FLOW_SENSOR_001",
        temperature=26.0,
        humidity=55.0,
        pressure=1016.0,
        timestamp=datetime.utcnow().isoformat(),
        location="Flow Demo"
    )
    
    await memory_source.consume(source_data)
    logger.info(f"Generated source data: {source_data.sensor_id}")
    
    # Simulate data processing and transformation
    retrieved_data = await memory_source.provide()
    
    # Transform sensor data to device status
    device_status = DeviceStatus(
        device_id=f"DEVICE_{retrieved_data.sensor_id}",
        status="online" if retrieved_data.temperature < 30 else "warning",
        last_seen=retrieved_data.timestamp,
        battery_level=90.0,
        firmware_version="1.5.0",
        location=retrieved_data.location
    )
    
    # Store transformed data in destination
    await memory_dest.consume(device_status, meta={
        "source": "data_flow_demo",
        "transformation": "sensor_to_device",
        "original_sensor": retrieved_data.sensor_id
    })
    
    logger.info(f"Transformed and stored device status: {device_status.device_id}")
    
    # Verify the flow
    final_data = await memory_dest.provide()
    logger.info(f"Final data in destination: {final_data.device_id} - {final_data.status}")


async def main():
    """Main demonstration function."""
    logger.info("🚀 Starting AAS Middleware Connector Demonstration")
    
    # Build the application
    builder = AppBuilder()
    app = builder.meta(
        name="connector_demo",
        version="1.0.0",
        description="Demonstration of all connector types"
    ).models([
        SensorData,
        DeviceStatus
    ).connector(
        "memory_sensor",
        MemoryConnector,
        SensorData
    ).connector(
        "memory_device", 
        MemoryConnector,
        DeviceStatus
    ).connector(
        "http_in",
        "HttpInConnector",
        DeviceStatus,
        config=HttpConnectorConfig(
            base_url="http://localhost:8001/api",
            timeout=5.0
        )
    ).connector(
        "http_out",
        "HttpOutConnector",
        DeviceStatus,
        config=HttpConnectorConfig(
            base_url="http://localhost:8002/api",
            timeout=5.0
        )
    ).connector(
        "sql_sensor",
        "SqlConnector",
        SensorData,
        config=SqlConnectorConfig(
            host="localhost",
            port=5432,
            database="demo_db",
            username="demo_user",
            password="demo_pass",
            table_name="sensor_data"
        )
    ).connector(
        "redis_sensor",
        "RedisConnector",
        SensorData,
        config=RedisConnectorConfig(
            host="localhost",
            port=6379,
            database=0,
            key_prefix="demo:"
        )
    ).build()
    
    try:
        # Start the application
        await app.start()
        logger.info("✅ Application started successfully")
        
        # Demonstrate each connector type
        await demonstrate_memory_connector(app)
        await demonstrate_http_connectors(app)
        await demonstrate_sql_connector(app)
        await demonstrate_redis_connector(app)
        await demonstrate_rest_api(app)
        await demonstrate_data_flow(app)
        
        logger.info("🎉 All demonstrations completed successfully!")
        
        # Show final status
        status = app.get_status()
        logger.info(f"Application status: {status}")
        
    except Exception as e:
        logger.error(f"❌ Demonstration failed: {e}")
        raise
    
    finally:
        # Stop the application
        await app.stop()
        logger.info("🛑 Application stopped")


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("🛑 Demonstration interrupted by user")
    except Exception as e:
        logger.error(f"💥 Fatal error: {e}")
        sys.exit(1)
