"""
Logging configuration for the Box Nesting Optimization System.
"""

import logging
import sys
import os
from pathlib import Path
from typing import Optional


def setup_logging(level: int = logging.INFO, 
                 log_file: Optional[str] = None,
                 enable_console: bool = True) -> None:
    """
    Setup comprehensive logging configuration.
    
    Args:
        level: Logging level
        log_file: Optional file path for file logging
        enable_console: Whether to enable console logging
    """
    # Create logger
    logger = logging.getLogger()
    logger.setLevel(level)
    
    # Clear existing handlers
    for handler in logger.handlers[:]:
        logger.removeHandler(handler)
    
    # Create formatter
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    
    # Console handler
    if enable_console:
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setLevel(level)
        console_handler.setFormatter(formatter)
        logger.addHandler(console_handler)
    
    # File handler
    if log_file:
        try:
            # Create logs directory if it doesn't exist
            log_path = Path(log_file)
            log_path.parent.mkdir(parents=True, exist_ok=True)
            
            file_handler = logging.FileHandler(log_file, encoding='utf-8')
            file_handler.setLevel(level)
            file_handler.setFormatter(formatter)
            logger.addHandler(file_handler)
            
            logging.info("File logging enabled: %s", log_file)
        except Exception as e:
            logging.error("Failed to setup file logging: %s", e)
    
    # Reduce verbosity for some noisy modules
    logging.getLogger('PySide6').setLevel(logging.WARNING)
    logging.getLogger('pyclipper').setLevel(logging.INFO)
    
    logging.info("Logging configured successfully (level: %s)", 
                 logging.getLevelName(level))


def get_logger(name: str) -> logging.Logger:
    """
    Get logger with given name.
    
    Args:
        name: Logger name
        
    Returns:
        Configured logger instance
    """
    return logging.getLogger(name)


class PerformanceLogger:
    """
    Performance logging utility for timing operations.
    """
    
    def __init__(self, operation_name: str, logger: Optional[logging.Logger] = None):
        """
        Initialize performance logger.
        
        Args:
            operation_name: Name of the operation being timed
            logger: Logger instance, creates new one if None
        """
        self.operation_name = operation_name
        self.logger = logger or get_logger(__name__)
        self.start_time = None
        
    def __enter__(self):
        """Start timing when entering context."""
        self.start_time = self._current_time()
        self.logger.debug("Starting operation: %s", self.operation_name)
        return self
        
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Log timing when exiting context."""
        if self.start_time is not None:
            elapsed = self._current_time() - self.start_time
            if exc_type is None:
                self.logger.info("Operation %s completed in %.3f seconds", 
                               self.operation_name, elapsed)
            else:
                self.logger.error("Operation %s failed after %.3f seconds: %s",
                                self.operation_name, elapsed, exc_val)
                
    def _current_time(self) -> float:
        """Get current time in seconds."""
        import time
        return time.time()
        
    def checkpoint(self, checkpoint_name: str) -> None:
        """
        Log checkpoint with elapsed time.
        
        Args:
            checkpoint_name: Name of the checkpoint
        """
        if self.start_time is not None:
            elapsed = self._current_time() - self.start_time
            self.logger.debug("Checkpoint %s: %.3f seconds", checkpoint_name, elapsed)


def log_function_call(func):
    """
    Decorator to log function calls and execution time.
    
    Args:
        func: Function to decorate
        
    Returns:
        Decorated function
    """
    def wrapper(*args, **kwargs):
        logger = get_logger(func.__module__)
        
        with PerformanceLogger(f"{func.__module__}.{func.__name__}", logger):
            result = func(*args, **kwargs)
            
        return result
        
    return wrapper