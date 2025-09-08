"""
Adapters for the middleware system.

This module contains adapters that provide interfaces to external
systems and persistence backends.
"""

from .connectors import (
    MemoryConnector,
    HttpInConnector,
    HttpOutConnector,
    HttpConnectorConfig,
    SqlConnector,
    SqlConnectorConfig,
    RedisConnector,
    RedisConnectorConfig
)

__all__ = [
    "MemoryConnector",
    "HttpInConnector",
    "HttpOutConnector", 
    "HttpConnectorConfig",
    "SqlConnector",
    "SqlConnectorConfig",
    "RedisConnector",
    "RedisConnectorConfig"
]
