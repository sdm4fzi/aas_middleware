"""
Ports for the middleware system.

This module contains the interfaces and protocols that define
the contracts between different parts of the system.
"""

from .connector import Connector
from .lifecycle import Connectable
from .discovery import ServiceDiscovery

__all__ = [
    "Connector",
    "Connectable", 
    "ServiceDiscovery"
]
