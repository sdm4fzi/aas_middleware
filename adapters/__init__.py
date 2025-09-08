"""
Adapters module for the middleware system.

This module contains adapters that implement the core protocols
for various external systems and technologies.
"""

from .connectors import *
from .mapping import *
from .discovery import *
from .web import *

__all__ = [
    # Connectors
    "MemoryConnector",
    "HttpInConnector", 
    "HttpOutConnector",
    "SqlConnector",
    "RedisConnector",
    
    # Mapping
    "BasyxFormatter",
    "PydanticMapper",
    
    # Discovery
    "ConsulServiceRegistry",
    
    # Web
    "RestAdapter",
    "GraphQLAdapter",
    "AdminAdapter",
    "SseAdapter",
]
