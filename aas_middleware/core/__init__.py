"""
Core functionality for the middleware system.

This module contains the fundamental components and utilities
that form the backbone of the middleware architecture.
"""

from .bindings import BindingRegistry, Binding
from .config_model import ConfigModel, ConfigField
from .events import EventBus, Event, EventHandler
from .instrumentation import Instrumentation, MetricsCollector
from .registries import Registry, RegistryEntry
from .errors import MiddlewareError, ConfigurationError, ConnectionError

__all__ = [
    "BindingRegistry",
    "Binding", 
    "ConfigModel",
    "ConfigField",
    "EventBus",
    "Event",
    "EventHandler",
    "Instrumentation",
    "MetricsCollector",
    "Registry",
    "RegistryEntry",
    "MiddlewareError",
    "ConfigurationError",
    "ConnectionError"
]
