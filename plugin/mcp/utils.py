"""
Odoo MCP Utilities Module

Shared utilities for the MCP package.
"""

import logging
import functools
from typing import Any, Callable, Optional, TypeVar

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger(__name__)

T = TypeVar('T')


def setup_logging(level: str = "INFO") -> None:
    """
    Setup logging for MCP modules.

    Args:
        level: Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL).
    """
    numeric_level = getattr(logging, level.upper(), logging.INFO)
    logging.getLogger("mcp").setLevel(numeric_level)
    logger.setLevel(numeric_level)


def handle_errors(
    default_return: Any = None,
    log_errors: bool = True,
    error_message: str = "An error occurred"
) -> Callable:
    """
    Decorator to handle errors in MCP functions.

    Args:
        default_return: Value to return on error.
        log_errors: Whether to log errors.
        error_message: Error message prefix.

    Returns:
        Decorated function.
    """
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            try:
                return func(*args, **kwargs)
            except Exception as e:
                if log_errors:
                    logger.error(f"{error_message}: {e}")
                return default_return
        return wrapper
    return decorator


def retry(
    max_attempts: int = 3,
    delay: float = 1.0,
    backoff: float = 2.0,
    exceptions: tuple = (Exception,)
) -> Callable:
    """
    Decorator to retry a function on failure.

    Args:
        max_attempts: Maximum number of attempts.
        delay: Initial delay between attempts.
        backoff: Backoff multiplier.
        exceptions: Exceptions to catch and retry.

    Returns:
        Decorated function.
    """
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            current_delay = delay
            last_exception = None

            for attempt in range(max_attempts):
                try:
                    return func(*args, **kwargs)
                except exceptions as e:
                    last_exception = e
                    if attempt < max_attempts - 1:
                        logger.warning(
                            f"Attempt {attempt + 1}/{max_attempts} failed: {e}. "
                            f"Retrying in {current_delay}s..."
                        )
                        import time
                        time.sleep(current_delay)
                        current_delay *= backoff
                    else:
                        logger.error(f"All {max_attempts} attempts failed")

            if last_exception:
                raise last_exception
            return None
        return wrapper
    return decorator


def log_execution(func: Callable) -> Callable:
    """
    Decorator to log function execution.

    Args:
        func: Function to decorate.

    Returns:
        Decorated function.
    """
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        logger.debug(f"Executing {func.__name__}...")
        try:
            result = func(*args, **kwargs)
            logger.debug(f"Completed {func.__name__}")
            return result
        except Exception as e:
            logger.error(f"Error in {func.__name__}: {e}")
            raise
    return wrapper


class RateLimiter:
    """Simple rate limiter for API calls."""

    def __init__(self, max_calls: int, time_window: float):
        """
        Initialize rate limiter.

        Args:
            max_calls: Maximum calls allowed.
            time_window: Time window in seconds.
        """
        self.max_calls = max_calls
        self.time_window = time_window
        self.calls = []

    def is_allowed(self) -> bool:
        """
        Check if a call is allowed.

        Returns:
            True if allowed, False otherwise.
        """
        import time
        now = time.time()

        # Remove old calls outside the time window
        self.calls = [t for t in self.calls if now - t < self.time_window]

        if len(self.calls) < self.max_calls:
            self.calls.append(now)
            return True
        return False

    def wait_time(self) -> float:
        """
        Get time to wait before next call is allowed.

        Returns:
            Wait time in seconds.
        """
        import time
        if not self.calls:
            return 0.0

        now = time.time()
        oldest = min(self.calls)
        return max(0.0, self.time_window - (now - oldest))


def safe_get(dictionary: dict, *keys, default: Any = None) -> Any:
    """
    Safely get nested dictionary value.

    Args:
        dictionary: Dictionary to get from.
        *keys: Keys to traverse.
        default: Default value if not found.

    Returns:
        Value or default.
    """
    current = dictionary
    for key in keys:
        if isinstance(current, dict):
            current = current.get(key)
            if current is None:
                return default
        else:
            return default
    return current


def format_error(error: Exception) -> str:
    """
    Format an exception for user display.

    Args:
        error: Exception to format.

    Returns:
        Formatted error string.
    """
    error_type = type(error).__name__
    error_msg = str(error)

    # Common error type mappings
    error_mapping = {
        "xmlrpc.client.Error": "XML-RPC Error",
        "requests.RequestException": "Network Error",
        "ConnectionError": "Connection Error",
        "TimeoutError": "Timeout Error"
    }

    friendly_type = error_mapping.get(error_type, error_type)

    return f"{friendly_type}: {error_msg}"


__all__ = [
    "setup_logging",
    "handle_errors",
    "retry",
    "log_execution",
    "RateLimiter",
    "safe_get",
    "format_error"
]
