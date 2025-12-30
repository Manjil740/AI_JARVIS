"""
Logger Module - Centralized logging for JARVIS
Supports both file and console logging with config-driven setup
"""

import logging
import logging.handlers
import os
import json
from pathlib import Path
from typing import Optional

_loggers = {}


def get_logger(name: str) -> logging.Logger:
    """
    Get or create a logger with the given name.
    Uses config-driven settings from config/config.json
    
    Args:
        name: Logger name (typically __name__)
    
    Returns:
        Configured logger instance
    """
    if name in _loggers:
        return _loggers[name]

    logger = logging.getLogger(name)
    
    # Avoid duplicate handlers
    if logger.handlers:
        return logger

    try:
        # Load config
        config_path = Path(__file__).parent.parent / "config" / "config.json"
        with open(config_path, 'r') as f:
            config = json.load(f)
        logging_config = config.get("logging", {})
    except Exception as e:
        # Fallback config if file not found
        logging_config = {
            "level": "INFO",
            "format": "%(asctime)s - %(name)s - %(levelname)s - %(message)s",
            "file_path": "/var/log/jarvis/jarvis.log",
            "max_bytes": 10485760,
            "backup_count": 5,
        }
        print(f"Warning: Using default logging config: {e}")

    # Set level
    level_name = logging_config.get("level", "INFO")
    log_level = getattr(logging, level_name.upper(), logging.INFO)
    logger.setLevel(log_level)

    # Format
    format_str = logging_config.get(
        "format",
        "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    )
    formatter = logging.Formatter(format_str)

    # File handler with rotation
    log_file = logging_config.get("file_path", "/var/log/jarvis/jarvis.log")
    max_bytes = logging_config.get("max_bytes", 10485760)
    backup_count = logging_config.get("backup_count", 5)

    try:
        log_dir = os.path.dirname(log_file)
        if log_dir and not os.path.exists(log_dir):
            os.makedirs(log_dir, exist_ok=True)

        file_handler = logging.handlers.RotatingFileHandler(
            log_file,
            maxBytes=max_bytes,
            backupCount=backup_count
        )
        file_handler.setLevel(log_level)
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)
    except Exception as e:
        print(f"Warning: Could not setup file logging to {log_file}: {e}")

    # Console handler
    console_handler = logging.StreamHandler()
    console_handler.setLevel(log_level)
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)

    _loggers[name] = logger
    return logger


def setup_logging(config: dict) -> None:
    """
    Setup logging for all JARVIS modules based on config dict
    
    Args:
        config: Configuration dictionary
    """
    logging_config = config.get("logging", {})
    level_name = logging_config.get("level", "INFO")
    log_level = getattr(logging, level_name.upper(), logging.INFO)
    
    # Update root logger
    logging.getLogger().setLevel(log_level)


def get_file_handler(log_file: str) -> Optional[logging.handlers.RotatingFileHandler]:
    """
    Create a rotating file handler
    
    Args:
        log_file: Path to log file
    
    Returns:
        RotatingFileHandler instance or None if error
    """
    try:
        log_dir = os.path.dirname(log_file)
        if log_dir:
            os.makedirs(log_dir, exist_ok=True)

        handler = logging.handlers.RotatingFileHandler(
            log_file,
            maxBytes=10485760,  # 10MB
            backupCount=5
        )
        return handler
    except Exception as e:
        print(f"Error creating file handler for {log_file}: {e}")
        return None