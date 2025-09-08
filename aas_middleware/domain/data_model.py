"""
Data model base class for the middleware system.

This module provides the base class for all data models in the system,
enabling type safety and validation.
"""

from typing import Any, Dict, List, Optional, Type, TypeVar
from pydantic import BaseModel, Field
import json


class DataModel(BaseModel):
    """
    Base class for all data models in the middleware system.
    
    This class provides common functionality for data models including
    serialization, validation, and metadata management.
    """
    
    class Config:
        """Pydantic configuration."""
        arbitrary_types_allowed = True
        extra = "allow"
        
    def to_dict(self) -> Dict[str, Any]:
        """
        Convert the model to a dictionary.
        
        Returns:
            Dictionary representation of the model
        """
        return self.dict()
        
    def to_json(self, **kwargs) -> str:
        """
        Convert the model to JSON string.
        
        Args:
            **kwargs: Additional arguments for json.dumps
            
        Returns:
            JSON string representation of the model
        """
        return self.json(**kwargs)
        
    @classmethod
    def from_dict(cls: Type['DataModel'], data: Dict[str, Any]) -> 'DataModel':
        """
        Create a model instance from a dictionary.
        
        Args:
            data: Dictionary data
            
        Returns:
            Model instance
        """
        return cls(**data)
        
    @classmethod
    def from_json(cls: Type['DataModel'], json_str: str) -> 'DataModel':
        """
        Create a model instance from a JSON string.
        
        Args:
            json_str: JSON string
            
        Returns:
            Model instance
        """
        data = json.loads(json_str)
        return cls.from_dict(data)
        
    def get_field_value(self, field_name: str) -> Any:
        """
        Get the value of a field by name.
        
        Args:
            field_name: Name of the field
            
        Returns:
            Field value
            
        Raises:
            AttributeError: If field doesn't exist
        """
        if not hasattr(self, field_name):
            raise AttributeError(f"Field '{field_name}' not found in {self.__class__.__name__}")
        return getattr(self, field_name)
        
    def set_field_value(self, field_name: str, value: Any) -> None:
        """
        Set the value of a field by name.
        
        Args:
            field_name: Name of the field
            value: Value to set
            
        Raises:
            AttributeError: If field doesn't exist
            ValueError: If value is invalid for the field
        """
        if not hasattr(self, field_name):
            raise AttributeError(f"Field '{field_name}' not found in {self.__class__.__name__}")
            
        # Validate the value if possible
        field_info = self.__fields__.get(field_name)
        if field_info:
            # Use pydantic validation
            validated_value = field_info.validate(value, {}, loc=field_name)
            setattr(self, field_name, validated_value)
        else:
            setattr(self, field_name, value)
            
    def get_model_info(self) -> Dict[str, Any]:
        """
        Get information about the model.
        
        Returns:
            Dictionary containing model metadata
        """
        return {
            "class_name": self.__class__.__name__,
            "module": self.__class__.__module__,
            "fields": list(self.__fields__.keys()),
            "field_types": {
                name: str(field.type_) 
                for name, field in self.__fields__.items()
            }
        }
        
    def copy(self, **kwargs) -> 'DataModel':
        """
        Create a copy of the model with optional field updates.
        
        Args:
            **kwargs: Field values to update in the copy
            
        Returns:
            New model instance
        """
        data = self.dict()
        data.update(kwargs)
        return self.__class__(**data)


# Type variable for generic operations
T = TypeVar('T', bound=DataModel)
