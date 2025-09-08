# RheoNet Middleware - Refactored Architecture

This repository contains the refactored middleware system based on the design outlined in `refactor_plan.md`. The new architecture provides a unified connector protocol, automatic persistence, and a fluent builder interface.

## Key Features

### 🚀 **Unified Connector Protocol**
- **Single interface**: All connectors implement `provide()`, `consume()`, and `receive()`
- **Automatic instrumentation**: Events are emitted automatically without connector authors needing to handle them
- **Lifecycle support**: Optional `connect()`/`disconnect()` for resource management

### 🗄️ **Persistence as Connectors**
- **Auto-generated**: Persistence connectors are created automatically when data models are registered
- **Multiple backends**: Support for memory, SQL, Redis, and HTTP persistence
- **Field-level**: Optional field-level persistence for hot fields

### 🔗 **Fluent Builder Interface**
- **Chainable API**: Build complex configurations with method chaining
- **Auto-wiring**: Automatic creation of persistence connectors and bindings
- **Type safety**: Full type hints and validation using Pydantic

### 📊 **Event-Driven Architecture**
- **Automatic events**: All connector operations emit events automatically
- **Observability**: Built-in monitoring and debugging capabilities
- **Integration ready**: Easy integration with external monitoring systems

## Architecture Overview

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Facade Layer  │    │   Core Layer    │    │  Adapters Layer │
│                 │    │                 │    │                 │
│ • AppBuilder    │───▶│ • Registries    │───▶│ • Connectors    │
│ • MiddlewareApp │    │ • EventBus      │    │ • Mappers       │
│ • ChainBuilder  │    │ • Bindings      │    │ • Formatters    │
└─────────────────┘    └─────────────────┘    └─────────────────┘
                                │
                       ┌─────────────────┐
                       │   Ports Layer   │
                       │                 │
                       │ • Connector     │
                       │ • Connectable   │
                       │ • ServiceRegistry│
                       └─────────────────┘
```

## Quick Start

### 1. Basic Setup

```python
from facade.builder import AppBuilder

# Create a simple middleware application
app = (
    AppBuilder()
        .meta(title="My MW", version="1.0.0")
        .persistence(kind="memory")
        .models("shop", types=["Order", "Product"])
        .build()
)
```

### 2. Add Connectors

```python
app = (
    AppBuilder()
        .connector("erp", kind="http_in", path="/erp/orders")
        .connector("database", kind="sql", dsn="postgresql://...")
        .build()
)
```

### 3. Create Bindings

```python
app = (
    AppBuilder()
        .bind("connector:erp", "persist:shop/Order", direction="push")
        .bind("persist:shop/Order", "connector:database", direction="push")
        .build()
)
```

### 4. Build Chains

```python
app = (
    AppBuilder()
        .chain("process_order")
            .receive("connector:erp")
            .map("erp_to_order")
            .consume("persist:shop/Order")
            .register()
        .build()
)
```

## Component Types

### Connectors
- **HTTP Input**: Receive data from external HTTP endpoints
- **HTTP Output**: Send data to external HTTP endpoints
- **SQL**: Database persistence with automatic schema management
- **Redis**: High-performance in-memory persistence
- **Memory**: Default in-memory persistence for development

### Mappers
- **Pydantic**: Type-safe data transformation using Pydantic models
- **Custom**: User-defined mapping functions
- **Schema-based**: Automatic mapping based on JSON schemas

### Formatters
- **JSON**: Standard JSON serialization/deserialization
- **Basyx**: AAS-specific formatting
- **Custom**: User-defined formatting functions

## Configuration

The system uses Pydantic models for configuration, providing:
- **Type safety**: All configuration is validated at runtime
- **Default values**: Sensible defaults for all components
- **Environment variables**: Support for environment-based configuration
- **Hot reloading**: Configuration can be updated without restart

## Event System

### Automatic Events
- `connector.provide.start/success/error`
- `connector.consume.start/success/error`
- `connector.receive.start/item/complete/error`
- `chain.execute`

### Custom Events
```python
# Subscribe to events
app.event_bus.subscribe("connector.provide.success", callback)

# Publish custom events
app.event_bus.publish("custom.event", data={"key": "value"}, source="my_component")
```

## Service Discovery

### Consul Integration
```python
app = (
    AppBuilder()
        .discover(kind="consul", url="http://consul:8500")
        .build()
)
```

### Auto-registration
- Connectors register with capabilities and I/O schemas
- Mappers and formatters register with input/output types
- Workflows register with execution metadata

## Development

### Project Structure
```
├── core/                 # Core runtime components
│   ├── events.py        # Event bus system
│   ├── registries.py    # Component registries
│   ├── bindings.py      # Binding system
│   └── instrumentation.py # Automatic event emission
├── ports/               # Protocol definitions
│   ├── connector.py     # Unified connector protocol
│   ├── lifecycle.py     # Optional lifecycle protocol
│   └── discovery.py     # Service discovery interface
├── domain/              # Domain models
│   └── data_model.py    # Base data model class
├── adapters/            # Protocol implementations
│   ├── connectors/      # Connector implementations
│   ├── mapping/         # Mapper implementations
│   └── discovery/       # Service discovery implementations
├── facade/              # High-level interfaces
│   ├── builder.py       # Fluent builder interface
│   └── app.py          # Main application class
└── utils/               # Utility functions
    ├── logging.py       # Logging configuration
    └── tracing.py       # Tracing utilities
```

### Running Examples
```bash
# Run the basic example
python example_usage.py

# Run with debug logging
python -c "
import logging
logging.basicConfig(level=logging.DEBUG)
import example_usage
"
```

## Migration from aas_middleware

### Key Changes
1. **Unified Protocol**: Single `Connector` protocol instead of separate `Provider`/`Consumer`/`Receiver`
2. **Auto-persistence**: No separate persistence port - persistence is just connectors
3. **Fluent Interface**: Builder pattern for configuration instead of imperative setup
4. **Event-driven**: Automatic event emission for all operations

### Migration Path
1. **Update imports**: Change from `aas_middleware.connect.connectors` to new structure
2. **Implement new protocol**: Update connectors to implement unified `Connector` protocol
3. **Use builder interface**: Replace imperative configuration with fluent builder
4. **Update persistence**: Remove persistence port usage, use persistence connectors instead

## Contributing

### Development Setup
1. Clone the repository
2. Install dependencies: `pip install -r requirements.txt`
3. Run tests: `pytest tests/`
4. Run examples: `python example_usage.py`

### Adding New Components
1. **Implement protocol**: Create class implementing the appropriate protocol
2. **Add to registry**: Register in the appropriate registry
3. **Add configuration**: Extend configuration models if needed
4. **Add tests**: Create comprehensive tests for the new component

## License

This project is licensed under the same terms as the original aas_middleware project.

## Support

For questions and support:
- Check the examples in `examples/`
- Review the configuration models in `core/config_model.py`
- Examine the protocol definitions in `ports/`
