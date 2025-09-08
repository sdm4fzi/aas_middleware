"""
Core module for the refactored middleware system.

This module contains the fundamental protocols, registries, and runtime components
that form the backbone of the middleware system.
"""

from .runtime import Runtime
from .events import EventBus
from .registries import ConnectorRegistry, MapperRegistry, FormatterRegistry, WorkflowRegistry
from .bindings import Address, Binding
from .sync_engine import SyncEngine
from .chain_runtime import ChainRuntime
from .errors import MiddlewareError
from .config_model import AppConfig, PersistenceBackendSpec
from .instrumentation import InstrumentedConnector

__all__ = [
    "Runtime",
    "EventBus", 
    "ConnectorRegistry",
    "MapperRegistry",
    "FormatterRegistry",
    "WorkflowRegistry",
    "Address",
    "Binding",
    "SyncEngine",
    "ChainRuntime",
    "MiddlewareError",
    "AppConfig",
    "PersistenceBackendSpec",
    "InstrumentedConnector",
]
