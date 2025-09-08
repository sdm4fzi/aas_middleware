# AAS Middleware Testing and Usage Guide

This guide covers how to test and use the AAS Middleware connectors, including unit tests, integration tests, and practical examples.

## 🚀 Quick Start

### Prerequisites

1. **Python 3.8+** installed
2. **Dependencies** installed (see requirements.txt)
3. **Test environment** ready

### Installation

```bash
# Install dependencies
pip install -r requirements.txt

# Verify installation
python -c "import aas_middleware; print('✅ Installation successful')"
```

## 🧪 Running Tests

### Test Runner Script

Use the provided test runner for easy execution:

```bash
# Run all tests
python run_tests.py

# Run only unit tests
python run_tests.py --unit

# Run only integration tests
python run_tests.py --integration

# Run with verbose output
python run_tests.py --verbose

# Run with coverage reporting
python run_tests.py --coverage
```

### Manual Test Execution

#### Unit Tests

```bash
# Run connector unit tests
pytest tests/test_connectors.py -v

# Run basic functionality tests
pytest tests/test_basic.py -v

# Run with coverage
pytest tests/test_connectors.py --cov=aas_middleware --cov-report=html
```

#### Integration Tests

```bash
# Run integration tests
pytest tests/test_integration.py -v

# Run specific test class
pytest tests/test_integration.py::TestIntegrationConnectors -v
```

### Test Structure

```
tests/
├── test_basic.py           # Basic functionality tests
├── test_connectors.py      # Connector unit tests
└── test_integration.py     # Integration tests via REST API
```

## 🔌 Connector Types

### 1. Memory Connector

**Purpose**: In-memory data storage for testing and development

**Features**:
- Fast in-memory operations
- Subscription mechanism
- Data streaming support
- Metadata handling

**Usage**:
```python
from aas_middleware.adapters.connectors import MemoryConnector
from aas_middleware.domain.data_model import DataModel

# Create connector
connector = MemoryConnector(DataModel)

# Connect
await connector.connect()

# Store data
await connector.consume(data, meta={"source": "test"})

# Retrieve data
data = await connector.provide()

# Stream data
async for item in connector.receive():
    process(item)

# Disconnect
await connector.disconnect()
```

### 2. HTTP Connectors

**Purpose**: HTTP-based data exchange with external systems

**Types**:
- `HttpInConnector`: Receives data from HTTP endpoints
- `HttpOutConnector`: Sends data to HTTP endpoints

**Features**:
- Configurable timeouts and retries
- Authentication support
- SSL/TLS configuration
- Background polling

**Usage**:
```python
from aas_middleware.adapters.connectors import (
    HttpInConnector, HttpOutConnector, HttpConnectorConfig
)

# Configuration
config = HttpConnectorConfig(
    base_url="http://api.example.com",
    timeout=30.0,
    auth={"username": "user", "password": "pass"}
)

# Create connectors
http_in = HttpInConnector(config, DataModel)
http_out = HttpOutConnector(config, DataModel)

# Connect
await http_in.connect()
await http_out.connect()

# Send data
await http_out.consume(data)

# Receive data
data = await http_in.provide()
```

### 3. SQL Connector

**Purpose**: Database persistence using PostgreSQL

**Features**:
- Connection pooling
- Automatic table creation
- JSONB data storage
- Transaction support

**Usage**:
```python
from aas_middleware.adapters.connectors import SqlConnector, SqlConnectorConfig

# Configuration
config = SqlConnectorConfig(
    host="localhost",
    port=5432,
    database="mydb",
    username="user",
    password="pass",
    table_name="sensor_data"
)

# Create connector
connector = SqlConnector(config, DataModel)

# Connect (creates table if needed)
await connector.connect()

# Store data
await connector.consume(data)

# Retrieve data
data = await connector.provide()

# Custom queries
results = await connector.query("SELECT * FROM sensor_data WHERE temperature > 20")
```

### 4. Redis Connector

**Purpose**: High-performance in-memory data storage

**Features**:
- Key-value operations
- TTL support
- Pub/Sub notifications
- Sorted set timeline

**Usage**:
```python
from aas_middleware.adapters.connectors import RedisConnector, RedisConnectorConfig

# Configuration
config = RedisConnectorConfig(
    host="localhost",
    port=6379,
    key_prefix="aas:",
    default_ttl=3600
)

# Create connector
connector = RedisConnector(config, DataModel)

# Connect
await connector.connect()

# Store data
await connector.consume(data)

# Get by specific key
data = await connector.get_by_key("custom_key")

# Set with custom TTL
await connector.set_by_key("temp_key", data, ttl=1800)
```

## 🌐 REST API Testing

### Starting the REST API

```python
from aas_middleware.facade.rest_api import MiddlewareRestAPI

# Create REST API
rest_api = MiddlewareRestAPI(app)

# Run synchronously
rest_api.run_sync(host="0.0.0.0", port=8000)

# Or run asynchronously
await rest_api.start(host="0.0.0.0", port=8000)
```

### API Endpoints

#### Health Check
```bash
GET /health
```

#### Connector Management
```bash
# List all connectors
GET /connectors

# Get connector status
GET /connectors/{connector_id}

# Connect connector
POST /connectors/{connector_id}/connect

# Disconnect connector
POST /connectors/{connector_id}/disconnect
```

#### Data Operations
```bash
# Provide data
GET /connectors/{connector_id}/provide

# Consume data
POST /connectors/{connector_id}/consume
{
    "connector_id": "memory_sensor",
    "data": {"name": "test", "value": 42},
    "meta": {"source": "test"}
}

# Receive data stream
GET /connectors/{connector_id}/receive?limit=10

# Clear data
POST /connectors/{connector_id}/clear

# Get count
GET /connectors/{connector_id}/count
```

### Testing with curl

```bash
# Health check
curl http://localhost:8000/health

# List connectors
curl http://localhost:8000/connectors

# Store data
curl -X POST http://localhost:8000/connectors/memory_sensor/consume \
  -H "Content-Type: application/json" \
  -d '{"connector_id": "memory_sensor", "data": {"name": "test", "value": 42}}'

# Retrieve data
curl http://localhost:8000/connectors/memory_sensor/provide
```

## 📊 Test Coverage

### Running Coverage

```bash
# Generate coverage report
pytest --cov=aas_middleware --cov-report=html

# View in browser
open htmlcov/index.html
```

### Coverage Targets

- **Unit Tests**: >90%
- **Integration Tests**: >80%
- **Overall Coverage**: >85%

## 🔧 Development Testing

### Adding New Tests

1. **Unit Tests**: Add to `tests/test_connectors.py`
2. **Integration Tests**: Add to `tests/test_integration.py`
3. **New Test Files**: Follow naming convention `test_*.py`

### Test Patterns

#### Async Test Setup
```python
@pytest.mark.asyncio
async def test_connector_operation():
    connector = create_test_connector()
    await connector.connect()
    
    try:
        # Test operations
        result = await connector.provide()
        assert result is not None
    finally:
        await connector.disconnect()
```

#### Mocking External Dependencies
```python
from unittest.mock import AsyncMock, patch

@patch('aiohttp.ClientSession')
async def test_http_connector(mock_session):
    mock_session.return_value = AsyncMock()
    # Test with mocked session
```

#### Fixture Usage
```python
@pytest.fixture
async def app():
    builder = AppBuilder()
    app = builder.meta(name="test").build()
    await app.start()
    yield app
    await app.stop()
```

## 🚨 Troubleshooting

### Common Issues

#### Import Errors
```bash
# Ensure package is installed in development mode
pip install -e .

# Check Python path
python -c "import sys; print(sys.path)"
```

#### Async Test Failures
```bash
# Ensure pytest-asyncio is installed
pip install pytest-asyncio

# Check for async markers
pytest --strict-markers
```

#### Connection Failures
- Verify external services are running
- Check configuration parameters
- Review firewall settings
- Test with mock implementations

### Debug Mode

```bash
# Run with debug logging
pytest --log-cli-level=DEBUG

# Run specific test with debug
pytest tests/test_connectors.py::TestMemoryConnector::test_connect_disconnect -s -v
```

## 📈 Performance Testing

### Load Testing

```bash
# Run performance tests
pytest tests/test_integration.py::TestPerformanceAndStress -v

# Monitor with profiling
python -m cProfile -o profile.stats example_all_connectors.py
```

### Benchmarking

```python
import time

# Measure operation time
start = time.time()
await connector.consume(data)
duration = time.time() - start
print(f"Operation took: {duration:.3f} seconds")
```

## 🔄 Continuous Integration

### GitHub Actions Example

```yaml
name: Tests
on: [push, pull_request]
jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v2
      - name: Set up Python
        uses: actions/setup-python@v2
        with:
          python-version: 3.9
      - name: Install dependencies
        run: pip install -r requirements.txt
      - name: Run tests
        run: python run_tests.py --coverage
```

## 📚 Additional Resources

### Documentation
- [API Reference](docs/API_reference/)
- [Tutorials](docs/Guides/)
- [Architecture Overview](README_REFACTOR.md)

### Examples
- [Basic Usage](example_usage.py)
- [All Connectors](example_all_connectors.py)
- [Integration Examples](tests/test_integration.py)

### Support
- Check existing issues
- Review test output
- Consult architecture documentation
- Review connector implementations

## 🎯 Next Steps

1. **Run Tests**: Execute `python run_tests.py`
2. **Explore Examples**: Study `example_all_connectors.py`
3. **Build Applications**: Use `AppBuilder` for your use cases
4. **Extend Connectors**: Implement custom connector types
5. **Contribute**: Add tests for new features

---

**Happy Testing! 🧪✨**
