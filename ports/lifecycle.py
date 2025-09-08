"""
Optional lifecycle protocol for connectors.

This protocol defines connect/disconnect functionality that connectors can implement
if they need to manage connection state.
"""

from typing import Protocol

class Connectable(Protocol):
    """
    Optional protocol for connectors that need to manage connection state.
    
    Connectors implementing this protocol can be connected/disconnected explicitly,
    which is useful for managing resources, authentication, and connection pooling.
    """
    
    async def connect(self) -> None:
        """
        Establish connection to the underlying service.
        
        This method should establish any necessary connections, authenticate,
        or prepare the connector for operation.
        
        Raises:
            ConnectionError: If the connection could not be established
            AuthenticationError: If authentication failed
        """
        ...

    async def disconnect(self) -> None:
        """
        Close connection to the underlying service.
        
        This method should clean up any resources, close connections,
        or perform any necessary cleanup when the connector is no longer needed.
        
        Raises:
            ConnectionError: If the disconnection failed
        """
        ...
