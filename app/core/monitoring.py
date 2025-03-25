"""
Monitoring utilities for the Instagram Carousel Generator.

This module provides context managers and utilities for performance monitoring.
"""
import functools
import logging
import time
from typing import Any, Callable, Optional, TypeVar, cast

# Set up logging
logger = logging.getLogger(__name__)

# Type variable for generic function types
F = TypeVar("F", bound=Callable[..., Any])


class PerformanceMonitoringContext:
    """
    Context manager for monitoring the performance of code blocks.

    This context manager measures the execution time of a code block
    and logs performance metrics.
    """

    def __init__(
        self,
        operation_name: str,
        logger_instance: Optional[logging.Logger] = None,
        log_level: int = logging.INFO,
        **extra_data,
    ):
        """
        Initialize the performance monitoring context.

        Args:
            operation_name: Name of the operation being monitored
            logger_instance: Logger instance to use (defaults to performance logger)
            log_level: Logging level for performance logs
            **extra_data: Additional data to include in logs
        """
        self.operation_name = operation_name
        self.logger = logger_instance or logging.getLogger("app.performance")
        self.log_level = log_level
        self.extra_data = extra_data
        self.start_time = None
        self.duration_ms = None

    def __enter__(self):
        """Start timing when entering the context."""
        self.start_time = time.time()
        self.logger.debug(
            f"Starting operation: {self.operation_name}",
            extra={"extra": {"operation": self.operation_name, **self.extra_data}},
        )

        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """
        Stop timing when exiting the context and log metrics.

        Args:
            exc_type: Exception type if an exception was raised
            exc_val: Exception value if an exception was raised
            exc_tb: Exception traceback if an exception was raised
        Returns:
            False to propagate exceptions
        """
        # Calculate duration
        self.duration_ms = (time.time() - self.start_time) * 1000
        # Determine success or failure
        success = exc_type is None
        status = "succeeded" if success else "failed"
        # Build log data
        log_data = {
            "operation": self.operation_name,
            "duration_ms": self.duration_ms,
            "success": success,
            **self.extra_data,
        }
        # Add exception info if an exception occurred
        if exc_type is not None:
            log_data["error_type"] = exc_type.__name__
            log_data["error"] = str(exc_val) if exc_val else "Unknown error"
        # Log at appropriate level
        level = logging.WARNING if not success else self.log_level
        self.logger.log(
            level,
            f"Operation '{self.operation_name}' {status} in {self.duration_ms:.2f}ms",
            extra={"extra": log_data},
        )
        # Return False to propagate exceptions

        return False


# Factory function for the context manager
def monitor_performance_context(operation_name: str, **extra_data):
    """
    Create a performance monitoring context.

    Args:
        operation_name: Name of the operation being monitored
        **extra_data: Additional data to include in logs
    Returns:
        PerformanceMonitoringContext instance
    """

    return PerformanceMonitoringContext(operation_name, **extra_data)


# Decorator for synchronous functions
def monitor_performance(operation_name: Optional[str] = None, **extra_data):
    """
    Monitor the performance of a function.

    Args:
        operation_name: Name of the operation (defaults to function name)
        **extra_data: Additional data to include in logs
    Returns:
        Decorated function
    """

    def decorator(func: F) -> F:
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            # Get operation name from function if not provided
            op_name = operation_name or func.__name__

            # Create context manager
            with monitor_performance_context(op_name, **extra_data):
                # Call the function
                return func(*args, **kwargs)

        return cast(F, wrapper)

    return decorator


# Decorator for asynchronous functions
def monitor_performance_async(operation_name: Optional[str] = None, **extra_data):
    """
    Monitor the performance of an async function.

    Args:
        operation_name: Name of the operation (defaults to function name)
        **extra_data: Additional data to include in logs
    Returns:
        Decorated async function
    """

    def decorator(func: F) -> F:
        @functools.wraps(func)
        async def wrapper(*args, **kwargs):
            # Get operation name from function if not provided
            op_name = operation_name or func.__name__

            # Create context manager
            with monitor_performance_context(op_name, **extra_data):
                # Call the function
                return await func(*args, **kwargs)

        return cast(F, wrapper)

    return decorator
