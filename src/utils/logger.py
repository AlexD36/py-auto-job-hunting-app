"""
Enhanced logging configuration for the Job Alert Notifier with rotating logs,
customizable log levels, and improved formatting.
"""
import logging
import os
from datetime import datetime
from logging.handlers import RotatingFileHandler
from typing import Optional, Union, Literal
import sys

# Type definitions for log levels
LogLevel = Union[
    int,
    Literal["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]
]

class LogConfig:
    """Configuration constants for logging"""
    DEFAULT_LOG_LEVEL: int = logging.INFO
    MAX_BYTES: int = 5 * 1024 * 1024  # 5 MB
    BACKUP_COUNT: int = 5
    DEFAULT_LOG_DIR: str = "logs"
    LOG_FORMAT: str = "%(asctime)s - %(name)s - %(levelname)s - [%(module)s:%(lineno)d] - %(message)s"

def get_log_level(level: LogLevel) -> int:
    """
    Convert string log level to logging constant if necessary
    
    Args:
        level: Log level as string or integer
        
    Returns:
        int: Logging level constant
        
    Raises:
        ValueError: If invalid log level provided
    """
    if isinstance(level, str):
        level_map = {
            "DEBUG": logging.DEBUG,
            "INFO": logging.INFO,
            "WARNING": logging.WARNING,
            "ERROR": logging.ERROR,
            "CRITICAL": logging.CRITICAL
        }
        if level.upper() not in level_map:
            raise ValueError(f"Invalid log level: {level}")
        return level_map[level.upper()]
    return level

def setup_logger(log_file: str) -> logging.Logger:
    """Set up and configure the application logger.
    
    Args:
        log_file (str): Path to the log file
        
    Returns:
        logging.Logger: Configured logger instance
    """
    logger = logging.getLogger("JobAlertNotifier")
    logger.setLevel(logging.INFO)
    
    # File handler with UTF-8 encoding
    file_handler = logging.FileHandler(log_file, encoding="utf-8")
    file_handler.setLevel(logging.INFO)
    
    # Console handler with UTF-8 encoding
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(logging.INFO)
    
    # Formatter
    formatter = logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - [%(module)s:%(lineno)d] - %(message)s")
    file_handler.setFormatter(formatter)
    console_handler.setFormatter(formatter)
    
    logger.addHandler(file_handler)
    logger.addHandler(console_handler)
    
    return logger

def get_logger() -> logging.Logger:
    """
    Get existing logger instance or create new one with default settings
    
    Returns:
        logging.Logger: Logger instance
    """
    logger = logging.getLogger("JobAlertNotifier")
    if not logger.handlers:
        logger = setup_logger()
    return logger 