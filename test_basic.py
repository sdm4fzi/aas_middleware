"""
Basic tests for the refactored middleware system.

These tests verify that the core components can be imported
and basic functionality works.
"""

import pytest
import asyncio
from unittest.mock import Mock


def test_imports():
    """Test that all core modules can be imported."""
    # Test core imports
    from core import (
        EventBus, ConnectorRegistry, MapperRegistry, 
        FormatterRegistry, WorkflowRegistry, Address, Binding
    )
    
    # Test ports imports
    from ports import Connector, Connectable, ServiceRegistry
    
    # Test domain imports
    from domain import DataModel
    
    # Test facade imports
    from facade import AppBuilder, MiddlewareApp
    
    # Test utils imports
    from utils import setup_logging
    
    assert True


def test_event_bus():
    """Test basic event bus functionality."""
    from core.events import EventBus
    
    bus = EventBus()
    
    # Test event publishing
    events = []
    bus.subscribe("test.event", lambda e: events.append(e))
    
    bus.publish("test.event", {"key": "value"}, "test_source")
    
    assert len(events) == 1
    assert events[0].name == "test.event"
    assert events[0].data["key"] == "value"


def test_registries():
    """Test basic registry functionality."""
    from core.registries import ConnectorRegistry
    
    registry = ConnectorRegistry()
    
    # Test adding and getting components
    mock_connector = Mock()
    registry.add("test_connector", mock_connector)
    
    retrieved = registry.get("test_connector")
    assert retrieved == mock_connector
    
    # Test listing components
    components = registry.list()
    assert "test_connector" in components


def test_data_model():
    """Test basic data model functionality."""
    from domain.data_model import DataModel
    
    class TestModel(DataModel):
        name: str
        value: int
    
    model = TestModel(name="test", value=42)
    
    # Test serialization
    data = model.to_dict()
    assert data["name"] == "test"
    assert data["value"] == 42
    
    # Test JSON serialization
    json_str = model.to_json()
    assert "test" in json_str
    assert "42" in json_str


def test_address():
    """Test address parsing and formatting."""
    from core.bindings import Address
    
    # Test address creation
    addr = Address("shop", "Order", "plan")
    assert str(addr) == "shop/Order/plan"
    
    # Test address parsing
    parsed = Address.parse("shop/Order/plan")
    assert parsed.data_model == "shop"
    assert parsed.model_id == "Order"
    assert parsed.field == "plan"


def test_binding():
    """Test binding creation and validation."""
    from core.bindings import Binding, BindingDirection
    
    # Test valid binding
    binding = Binding(
        id="test_binding",
        source="connector:source",
        target="connector:target",
        direction=BindingDirection.PUSH
    )
    
    assert binding.source == "connector:source"
    assert binding.target == "connector:target"
    
    # Test invalid binding (same source and target)
    with pytest.raises(ValueError):
        Binding(
            id="invalid",
            source="connector:same",
            target="connector:same",
            direction=BindingDirection.PUSH
        )


def test_app_builder():
    """Test basic app builder functionality."""
    from facade.builder import AppBuilder
    
    builder = AppBuilder()
    
    # Test basic configuration
    builder.meta(title="Test App", version="1.0.0")
    assert builder.config.metadata["title"] == "Test App"
    
    # Test persistence configuration
    builder.persistence(kind="memory")
    assert builder.config.persistence.kind == "memory"
    
    # Test model registration
    builder.models("test", ["Order", "Product"])
    assert len(builder.config.models) == 1
    assert builder.config.models[0].name == "test"


def test_chain_builder():
    """Test chain builder functionality."""
    from facade.builder import AppBuilder
    
    builder = AppBuilder()
    chain_builder = builder.chain("test_chain")
    
    # Test chain step addition
    chain_builder.receive("connector:source")
    chain_builder.consume("connector:target")
    
    assert len(chain_builder.steps) == 2
    assert chain_builder.steps[0]["type"] == "receive"
    assert chain_builder.steps[1]["type"] == "consume"
    
    # Test chain registration
    app_builder = chain_builder.register()
    assert app_builder is builder


@pytest.mark.asyncio
async def test_middleware_app():
    """Test basic middleware app functionality."""
    from facade.builder import AppBuilder
    from facade.app import MiddlewareApp
    
    # Build a simple app
    builder = AppBuilder()
    builder.meta(title="Test", version="1.0.0")
    builder.persistence(kind="memory")
    
    app = builder.build()
    
    # Test app creation
    assert isinstance(app, MiddlewareApp)
    assert app.config.metadata["title"] == "Test"
    
    # Test app status
    status = app.get_status()
    assert "running" in status
    assert "config" in status


if __name__ == "__main__":
    # Run tests
    pytest.main([__file__, "-v"])
