"""
Enhanced logging configuration for the Job Alert Notifier with rotating logs,
customizable log levels, and improved formatting.
"""
import logging
import os
from datetime import datetime
from logging.handlers import RotatingFileHandler
from typing import Optional, Union, Literal

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

def setup_logger(
    log_file: Optional[str] = None,
    level: LogLevel = LogConfig.DEFAULT_LOG_LEVEL
) -> logging.Logger:
    """
    Configure and return a logger instance with rotating file handler
    
    Args:
        log_file: Path to the log file (optional)
        level: Logging level (default: INFO)
        
    Returns:
        logging.Logger: Configured logger instance
    """
    # Convert log level if string
    log_level = get_log_level(level)
    
    # Create logger
    logger = logging.getLogger("JobAlertNotifier")
    
    # Return existing logger if already configured
    if logger.handlers:
        return logger
    
    # Set log level
    logger.setLevel(log_level)
    
    # Create formatter
    formatter = logging.Formatter(LogConfig.LOG_FORMAT)
    
    # Setup file handling
    if log_file is None:
        # Create default logs directory
        os.makedirs(LogConfig.DEFAULT_LOG_DIR, exist_ok=True)
        
        # Generate timestamp-based log filename
        timestamp = datetime.now().strftime("%Y-%m-%d")
        log_file = os.path.join(
            LogConfig.DEFAULT_LOG_DIR,
            f"{timestamp}-notifications.log"
        )
    else:
        # Ensure custom log directory exists
        os.makedirs(os.path.dirname(log_file), exist_ok=True)
    
    # Setup rotating file handler
    file_handler = RotatingFileHandler(
        log_file,
        maxBytes=LogConfig.MAX_BYTES,
        backupCount=LogConfig.BACKUP_COUNT
    )
    file_handler.setFormatter(formatter)
    logger.addHandler(file_handler)
    
    # Console handler
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)
    
    # Log initial setup information
    logger.debug(f"Logger initialized with level {logging.getLevelName(log_level)}")
    logger.debug(f"Log file: {log_file}")
    
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