"""
JARVIS - Voice AI Assistant Package
Main package initialization
"""

__version__ = "1.0.0"
__author__ = "JARVIS Dev Team"
__description__ = "Local Voice AI Assistant for Linux"

import sys
import os

# Ensure package imports work correctly
_package_dir = os.path.dirname(os.path.abspath(__file__))
if _package_dir not in sys.path:
    sys.path.insert(0, _package_dir)

from jarvis.logger import get_logger
from jarvis.utils import load_config

__all__ = [
    "get_logger",
    "load_config",
    "__version__",
]

# Initialize logger on import
logger = get_logger(__name__)
logger.info(f"JARVIS v{__version__} initialized")