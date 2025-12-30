"""
Intelligent Error Handler - Advanced error handling and recovery
Provides context-aware error messages and automatic recovery strategies
"""

import traceback
import sys
from typing import Optional, Dict, Any, Tuple, Callable
from enum import Enum
from datetime import datetime

from jarvis.logger import get_logger

logger = get_logger(__name__)


class ErrorSeverity(Enum):
    """Error severity levels"""
    DEBUG = 0
    INFO = 1
    WARNING = 2
    ERROR = 3
    CRITICAL = 4


class ErrorContext:
    """Context information for errors"""

    def __init__(self, error_type: str, severity: ErrorSeverity):
        """
        Initialize error context
        
        Args:
            error_type: Type of error
            severity: Severity level
        """
        self.error_type = error_type
        self.severity = severity
        self.timestamp = datetime.now()
        self.traceback_info = None
        self.user_message = None
        self.recovery_options = []
        self.metadata = {}

    def add_traceback(self):
        """Add current traceback information"""
        self.traceback_info = traceback.format_exc()

    def add_user_message(self, message: str):
        """Add user-friendly message"""
        self.user_message = message

    def add_recovery_option(self, option: str, description: str = ""):
        """Add a recovery option"""
        self.recovery_options.append({
            'option': option,
            'description': description,
        })

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            'error_type': self.error_type,
            'severity': self.severity.name,
            'timestamp': self.timestamp.isoformat(),
            'user_message': self.user_message,
            'recovery_options': self.recovery_options,
            'metadata': self.metadata,
        }


class ErrorHandler:
    """
    Advanced error handling system
    """

    # Error type to handler mapping
    ERROR_HANDLERS = {}

    def __init__(self):
        """Initialize error handler"""
        self.error_history = []
        self.max_history = 100
        self.error_counters = {}

    def register_handler(self, error_type: str, handler: Callable):
        """
        Register error handler for specific type
        
        Args:
            error_type: Error type string
            handler: Handler function
        """
        self.ERROR_HANDLERS[error_type] = handler
        logger.info(f"Registered handler for: {error_type}")

    def handle_error(self, error: Exception, context: str = "") -> ErrorContext:
        """
        Handle an exception with context
        
        Args:
            error: Exception instance
            context: Context description
        
        Returns:
            ErrorContext with handling information
        """
        error_type = type(error).__name__
        severity = self._determine_severity(error_type)

        # Create error context
        ctx = ErrorContext(error_type, severity)
        ctx.add_traceback()

        if context:
            ctx.metadata['context'] = context

        # Get user message
        user_msg = self._get_user_message(error_type, str(error))
        ctx.add_user_message(user_msg)

        # Add recovery options
        self._add_recovery_options(ctx, error_type)

        # Log error
        logger.log(
            level=severity.value * 10 + 20,  # Convert to logging level
            msg=f"{error_type}: {str(error)}",
            exc_info=True
        )

        # Add to history
        self._add_to_history(ctx)

        # Call specific handler if registered
        if error_type in self.ERROR_HANDLERS:
            handler = self.ERROR_HANDLERS[error_type]
            try:
                handler(error, ctx)
            except Exception as e:
                logger.error(f"Error handler failed: {e}")

        return ctx

    def _determine_severity(self, error_type: str) -> ErrorSeverity:
        """Determine error severity based on type"""
        critical_errors = [
            'SystemExit', 'KeyboardInterrupt', 'SystemError',
            'MemoryError', 'RecursionError', 'RuntimeError'
        ]

        if error_type in critical_errors:
            return ErrorSeverity.CRITICAL
        elif error_type in ['ValueError', 'TypeError', 'AttributeError']:
            return ErrorSeverity.ERROR
        elif error_type in ['IOError', 'OSError', 'FileNotFoundError']:
            return ErrorSeverity.WARNING
        else:
            return ErrorSeverity.ERROR

    def _get_user_message(self, error_type: str, error_msg: str) -> str:
        """Get user-friendly error message"""
        messages = {
            'FileNotFoundError': f"File not found. Please check the file path.",
            'PermissionError': "Access denied. Please check permissions.",
            'ValueError': f"Invalid value provided: {error_msg}",
            'TypeError': f"Type error: {error_msg}",
            'ConnectionError': "Connection failed. Check network.",
            'TimeoutError': "Operation timed out. Try again.",
            'KeyError': f"Missing key: {error_msg}",
            'IndexError': "Index out of range.",
            'AttributeError': f"Attribute error: {error_msg}",
            'ImportError': f"Failed to import: {error_msg}",
            'RuntimeError': f"Runtime error: {error_msg}",
        }

        return messages.get(error_type, f"An error occurred: {error_msg}")

    def _add_recovery_options(self, ctx: ErrorContext, error_type: str):
        """Add recovery options based on error type"""
        options_map = {
            'FileNotFoundError': [
                ('check_path', 'Check if file path is correct'),
                ('create_file', 'Create the missing file'),
                ('use_default', 'Use default file'),
            ],
            'PermissionError': [
                ('retry', 'Retry with different permissions'),
                ('use_sudo', 'Try with sudo'),
                ('check_permissions', 'Check file permissions'),
            ],
            'ConnectionError': [
                ('retry', 'Retry connection'),
                ('check_network', 'Check network connectivity'),
                ('offline_mode', 'Switch to offline mode'),
            ],
            'TimeoutError': [
                ('retry', 'Retry the operation'),
                ('increase_timeout', 'Increase timeout value'),
                ('cancel', 'Cancel the operation'),
            ],
            'MemoryError': [
                ('free_memory', 'Free up memory'),
                ('reduce_data', 'Reduce data size'),
                ('restart', 'Restart the application'),
            ],
        }

        if error_type in options_map:
            for option, description in options_map[error_type]:
                ctx.add_recovery_option(option, description)

    def _add_to_history(self, ctx: ErrorContext):
        """Add error to history"""
        self.error_history.append(ctx)

        # Increment counter
        error_type = ctx.error_type
        self.error_counters[error_type] = self.error_counters.get(error_type, 0) + 1

        # Remove old entries if exceeding limit
        if len(self.error_history) > self.max_history:
            self.error_history.pop(0)

    def get_error_summary(self) -> Dict[str, Any]:
        """Get summary of recent errors"""
        return {
            'total_errors': len(self.error_history),
            'error_types': self.error_counters.copy(),
            'recent_errors': [e.to_dict() for e in self.error_history[-5:]],
        }

    def clear_history(self):
        """Clear error history"""
        self.error_history.clear()
        self.error_counters.clear()


class AudioErrorHandler:
    """Handle audio-specific errors"""

    @staticmethod
    def handle_microphone_error(error: Exception) -> Tuple[bool, str]:
        """Handle microphone errors"""
        if 'permission' in str(error).lower():
            return False, "Microphone access denied. Check audio permissions."
        elif 'not found' in str(error).lower():
            return False, "Microphone not found. Check hardware."
        else:
            return False, f"Microphone error: {str(error)}"

    @staticmethod
    def handle_speaker_error(error: Exception) -> Tuple[bool, str]:
        """Handle speaker errors"""
        if 'permission' in str(error).lower():
            return False, "Speaker access denied. Check audio permissions."
        elif 'not found' in str(error).lower():
            return False, "Speaker not found. Check hardware."
        else:
            return False, f"Speaker error: {str(error)}"

    @staticmethod
    def handle_tts_error(error: Exception) -> Tuple[bool, str]:
        """Handle text-to-speech errors"""
        if 'no provider' in str(error).lower():
            return False, "No TTS provider available. Install pyttsx3."
        else:
            return False, f"TTS error: {str(error)}"

    @staticmethod
    def handle_stt_error(error: Exception) -> Tuple[bool, str]:
        """Handle speech-to-text errors"""
        if 'no microphone' in str(error).lower():
            return False, "No microphone detected."
        elif 'timeout' in str(error).lower():
            return False, "No speech detected. Please try again."
        else:
            return False, f"STT error: {str(error)}"


class NetworkErrorHandler:
    """Handle network-related errors"""

    @staticmethod
    def handle_api_error(error: Exception) -> Tuple[bool, str]:
        """Handle API errors"""
        error_str = str(error).lower()

        if 'timeout' in error_str:
            return False, "API request timed out. Try again later."
        elif '401' in error_str or 'unauthorized' in error_str:
            return False, "Invalid API key. Check your credentials."
        elif '429' in error_str or 'rate limit' in error_str:
            return False, "Rate limit exceeded. Wait before retrying."
        elif '503' in error_str or 'unavailable' in error_str:
            return False, "Service unavailable. Try again later."
        elif 'connection' in error_str:
            return False, "Connection failed. Check network."
        else:
            return False, f"API error: {str(error)}"

    @staticmethod
    def handle_connection_error(error: Exception) -> Tuple[bool, str]:
        """Handle connection errors"""
        return False, "Connection failed. Check network connectivity."


class FileOperationErrorHandler:
    """Handle file operation errors"""

    @staticmethod
    def handle_file_error(error: Exception) -> Tuple[bool, str]:
        """Handle file operation errors"""
        error_str = str(error).lower()

        if 'permission' in error_str:
            return False, "Permission denied. Check file permissions."
        elif 'no such file' in error_str or 'not found' in error_str:
            return False, "File not found. Check the file path."
        elif 'read only' in error_str:
            return False, "File is read-only. Change permissions to edit."
        elif 'exists' in error_str:
            return False, "File already exists."
        else:
            return False, f"File error: {str(error)}"


class ErrorRecovery:
    """Automatic error recovery strategies"""

    @staticmethod
    def retry_with_backoff(func: Callable, max_retries: int = 3, backoff_factor: float = 2.0) -> Optional[Any]:
        """
        Retry a function with exponential backoff
        
        Args:
            func: Function to retry
            max_retries: Maximum number of retries
            backoff_factor: Backoff multiplication factor
        
        Returns:
            Function result or None
        """
        import time

        for attempt in range(max_retries):
            try:
                return func()
            except Exception as e:
                if attempt == max_retries - 1:
                    logger.error(f"Max retries exceeded: {e}")
                    raise

                wait_time = backoff_factor ** attempt
                logger.warning(f"Retry {attempt + 1}/{max_retries} after {wait_time}s: {e}")
                time.sleep(wait_time)

        return None

    @staticmethod
    def fallback(primary_func: Callable, fallback_func: Callable) -> Optional[Any]:
        """
        Try primary function, fall back to secondary
        
        Args:
            primary_func: Primary function
            fallback_func: Fallback function
        
        Returns:
            Result from primary or fallback
        """
        try:
            return primary_func()
        except Exception as e:
            logger.warning(f"Primary failed, trying fallback: {e}")
            try:
                return fallback_func()
            except Exception as fe:
                logger.error(f"Fallback also failed: {fe}")
                return None

    @staticmethod
    def safe_execute(func: Callable, default_value: Any = None) -> Any:
        """
        Execute function safely with default return
        
        Args:
            func: Function to execute
            default_value: Default return value on error
        
        Returns:
            Function result or default value
        """
        try:
            return func()
        except Exception as e:
            logger.error(f"Safe execution failed: {e}")
            return default_value


# Global error handler instance
_error_handler = ErrorHandler()


def get_error_handler() -> ErrorHandler:
    """Get global error handler"""
    return _error_handler


def handle_exception(func: Callable) -> Callable:
    """
    Decorator for automatic exception handling
    
    Args:
        func: Function to wrap
    
    Returns:
        Wrapped function
    """
    def wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except Exception as e:
            ctx = _error_handler.handle_error(e, context=f"In {func.__name__}")
            logger.error(f"Exception in {func.__name__}: {ctx.user_message}")
            return None

    return wrapper