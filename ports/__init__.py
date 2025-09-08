"""
Ports module defining the core protocols for the middleware system.

This module contains the abstract interfaces that all adapters must implement.
"""

from .connector import Connector
from .lifecycle import Connectable
from .discovery import ServiceRegistry

__all__ = [
    "Connector",
    "Connectable", 
    "ServiceRegistry",
]
