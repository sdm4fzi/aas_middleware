"""
Logging utilities for the middleware system.

This module provides logging configuration and utilities
for consistent logging across the system.
"""

import logging
import logging.config
from typing import Dict, Any, Optional
import sys


def setup_logging(
    level: str = "INFO",
    format_string: Optional[str] = None,
    log_file: Optional[str] = None,
    config: Optional[Dict[str, Any]] = None
) -> None:
    """
    Setup logging configuration for the middleware system.
    
    Args:
        level: Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        format_string: Custom log format string
        log_file: Optional log file path
        config: Optional logging configuration dictionary
    """
    if config:
        # Use provided configuration
        logging.config.dictConfig(config)
        return
        
    # Default format
    if not format_string:
        format_string = (
            "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
        )
        
    # Create formatter
    formatter = logging.Formatter(format_string)
    
    # Setup root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(getattr(logging, level.upper()))
    
    # Clear existing handlers
    root_logger.handlers.clear()
    
    # Console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(formatter)
    root_logger.addHandler(console_handler)
    
    # File handler (if specified)
    if log_file:
        file_handler = logging.FileHandler(log_file)
        file_handler.setFormatter(formatter)
        root_logger.addHandler(file_handler)
        
    # Set specific logger levels
    logging.getLogger("asyncio").setLevel(logging.WARNING)
    logging.getLogger("urllib3").setLevel(logging.WARNING)
    
    logging.info(f"Logging configured with level: {level}")


def get_logger(name: str) -> logging.Logger:
    """
    Get a logger with the given name.
    
    Args:
        name: Logger name
        
    Returns:
        Configured logger instance
    """
    return logging.getLogger(name)


def set_log_level(logger_name: str, level: str) -> None:
    """
    Set the log level for a specific logger.
    
    Args:
        logger_name: Name of the logger
        level: Log level to set
    """
    logger = logging.getLogger(logger_name)
    logger.setLevel(getattr(logging, level.upper()))


def add_file_handler(
    logger_name: str, 
    log_file: str, 
    level: str = "INFO"
) -> None:
    """
    Add a file handler to a specific logger.
    
    Args:
        logger_name: Name of the logger
        log_file: Path to the log file
        level: Log level for the file handler
    """
    logger = logging.getLogger(logger_name)
    
    # Check if file handler already exists
    for handler in logger.handlers:
        if isinstance(handler, logging.FileHandler) and handler.baseFilename == log_file:
            return
            
    # Create formatter
    formatter = logging.Formatter(
        "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    )
    
    # Create and add file handler
    file_handler = logging.FileHandler(log_file)
    file_handler.setLevel(getattr(logging, level.upper()))
    file_handler.setFormatter(formatter)
    logger.addHandler(file_handler)
    
    logger.info(f"Added file handler: {log_file}")


def setup_structured_logging(
    level: str = "INFO",
    include_timestamp: bool = True,
    include_logger_name: bool = True,
    include_level: bool = True
) -> None:
    """
    Setup structured logging with JSON format.
    
    Args:
        level: Logging level
        include_timestamp: Whether to include timestamp
        include_logger_name: Whether to include logger name
        include_level: Whether to include log level
    """
    import json
    
    class StructuredFormatter(logging.Formatter):
        def format(self, record):
            log_entry = {
                "message": record.getMessage()
            }
            
            if include_timestamp:
                log_entry["timestamp"] = self.formatTime(record)
                
            if include_logger_name:
                log_entry["logger"] = record.name
                
            if include_level:
                log_entry["level"] = record.levelname
                
            # Add extra fields if present
            if hasattr(record, 'extra_fields'):
                log_entry.update(record.extra_fields)
                
            return json.dumps(log_entry)
    
    # Setup root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(getattr(logging, level.upper()))
    
    # Clear existing handlers
    root_logger.handlers.clear()
    
    # Console handler with structured formatter
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(StructuredFormatter())
    root_logger.addHandler(console_handler)
    
    logging.info("Structured logging configured")
