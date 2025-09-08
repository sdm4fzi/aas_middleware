"""
Error hierarchy for the middleware system.

This module defines the base exception classes and specific error types
used throughout the middleware system.
"""

class MiddlewareError(Exception):
    """Base exception for all middleware errors."""
    
    def __init__(self, message: str, details: dict | None = None):
        super().__init__(message)
        self.details = details or {}


class ConnectionError(MiddlewareError):
    """Raised when a connection to an external service fails."""
    pass


class AuthenticationError(MiddlewareError):
    """Raised when authentication to an external service fails."""
    pass


class ConfigurationError(MiddlewareError):
    """Raised when there's an error in the system configuration."""
    pass


class ValidationError(MiddlewareError):
    """Raised when data validation fails."""
    pass


class WorkflowError(MiddlewareError):
    """Raised when a workflow execution fails."""
    pass


class ChainError(MiddlewareError):
    """Raised when a chain execution fails."""
    pass


class RegistryError(MiddlewareError):
    """Raised when there's an error in a registry operation."""
    pass


class BindingError(MiddlewareError):
    """Raised when there's an error in binding operations."""
    pass


class PersistenceError(MiddlewareError):
    """Raised when there's an error in persistence operations."""
    pass
