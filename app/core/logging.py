"""
Set up logging configuration for the Instagram Carousel Generator.

This module provides a comprehensive logging setup with structured JSON logs,
configurable log levels, and support for various logging handlers.
It is designed to be easily integrated with external monitoring systems.
"""
import json
import logging
import socket
import sys
import time
import traceback
from datetime import datetime
from logging.handlers import RotatingFileHandler, TimedRotatingFileHandler
from pathlib import Path
from typing import Any, Dict, Optional

from app.core.config import settings


# JSON Log formatter for structured logging
class JSONFormatter(logging.Formatter):
    """
    JSON formatter for structured logging.

    Formats log records as JSON objects for better parsing by log aggregation tools.
    """

    def __init__(self, include_hostname: bool = True, **kwargs):
        """
        Initialize the JSON formatter.

        Args:
            include_hostname: Whether to include the hostname in logs
            **kwargs: Additional fields to include in every log entry
        """
        super().__init__()
        self.include_hostname = include_hostname
        self.hostname = socket.gethostname() if include_hostname else None
        self.additional_fields = kwargs

    def format(self, record: logging.LogRecord) -> str:
        """
        Format a log record as a JSON string.

        Args:
            record: The log record to format
        Returns:
            Formatted JSON string
        """
        log_data = {
            "timestamp": datetime.now().isoformat(),
            "level": record.levelname,
            "message": record.getMessage(),
            "logger": record.name,
            "module": record.module,
            "function": record.funcName,
            "line": record.lineno,
            "process_id": record.process,
            "thread_id": record.thread,
        }
        # Add hostname if configured
        if self.include_hostname:
            log_data["hostname"] = self.hostname
        # Add environment info
        log_data["environment"] = "production" if settings.PRODUCTION else "development"
        # Add any additional configured fields
        log_data.update(self.additional_fields)
        # Add extra fields from the log record
        if hasattr(record, "extra") and isinstance(record.extra, dict):
            log_data.update(record.extra)
        # Add exception info if present
        if record.exc_info:
            log_data["exception"] = {
                "type": record.exc_info[0].__name__,
                "message": str(record.exc_info[1]),
                "traceback": traceback.format_exception(*record.exc_info),
            }
        # Add request info if present
        if hasattr(record, "request_id"):
            log_data["request_id"] = record.request_id
        # Add performance metrics if present
        if hasattr(record, "duration_ms"):
            log_data["duration_ms"] = record.duration_ms
        return json.dumps(log_data, default=str)


class RequestAdapter(logging.LoggerAdapter):
    """Logger adapter that adds request-specific information to log records."""

    def __init__(self, logger, request_id: str):
        """
        Initialize the request adapter.

        Args:
            logger: The logger to adapt
            request_id: The request ID to add to log records
        """
        super().__init__(logger, {"request_id": request_id})
        self.request_id = request_id

    def process(self, msg, kwargs):
        """
        Process the log record before it's logged.

        Args:
            msg: The log message
            kwargs: Additional arguments
        Returns:
            Processed message and kwargs
        """
        # Ensure 'extra' exists in kwargs
        if "extra" not in kwargs:
            kwargs["extra"] = {}
        # Add request_id to extra
        kwargs["extra"]["request_id"] = self.request_id
        return msg, kwargs


def get_log_file_path() -> Optional[Path]:
    """
    Get the path for log files.

    Returns:
        Path to the log directory or None if logging to file is disabled
    """
    if not settings.ENABLE_FILE_LOGGING:
        return None
    # Use configured log path or default
    log_dir = settings.LOG_DIR if hasattr(settings, "LOG_DIR") else Path(settings.BASE_DIR) / "logs"
    # Create directory if it doesn't exist
    if not log_dir.exists():
        log_dir.mkdir(parents=True, exist_ok=True)
    return log_dir


def get_console_handler() -> logging.Handler:
    """
    Create a console handler for logging.

    Returns:
        Configured console handler
    """
    console_handler = logging.StreamHandler(sys.stdout)
    # Use JSON formatter in production, simpler formatter in development
    if settings.PRODUCTION:
        formatter = JSONFormatter()
    else:
        # More readable format for development
        formatter = logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s")
    console_handler.setFormatter(formatter)
    return console_handler


def get_file_handler() -> Optional[logging.Handler]:
    """
    Create a file handler for logging.

    Returns:
        Configured file handler or None if file logging is disabled
    """
    log_dir = get_log_file_path()
    if not log_dir:
        return None
    # Determine log file path
    log_file = log_dir / f"{settings.PROJECT_NAME.lower().replace(' ', '_')}.log"
    # Choose handler type based on settings
    if settings.LOG_ROTATION_TYPE == "size":
        handler = RotatingFileHandler(
            log_file, maxBytes=settings.LOG_MAX_SIZE, backupCount=settings.LOG_BACKUP_COUNT
        )
    else:  # time-based rotation
        handler = TimedRotatingFileHandler(
            log_file,
            when=settings.LOG_ROTATION_WHEN,
            interval=settings.LOG_ROTATION_INTERVAL,
            backupCount=settings.LOG_BACKUP_COUNT,
        )
    # Always use JSON formatter for file logging
    formatter = JSONFormatter()
    handler.setFormatter(formatter)
    return handler


def configure_logging():
    """
    Configure logging for the application.

    Sets up handlers, formatters, and log levels.
    """
    # Get root logger
    root_logger = logging.getLogger()
    # Set global log level from settings
    log_level = getattr(logging, settings.LOG_LEVEL.upper(), logging.INFO)
    root_logger.setLevel(log_level)
    # Remove existing handlers
    for handler in root_logger.handlers[:]:
        root_logger.removeHandler(handler)
    # Add console handler
    root_logger.addHandler(get_console_handler())
    # Add file handler if enabled
    file_handler = get_file_handler()
    if file_handler:
        root_logger.addHandler(file_handler)
    # Configure library loggers
    configure_library_loggers()
    logging.info(f"Logging configured with level {settings.LOG_LEVEL}")


def configure_library_loggers():
    """Configure third-party library loggers to reduce noise."""
    # List of noisy loggers to configure
    library_loggers = {
        "uvicorn": logging.WARNING,
        "uvicorn.access": logging.WARNING,
        "uvicorn.error": logging.ERROR,
        "fastapi": logging.WARNING,
        "PIL": logging.WARNING,
        "httpx": logging.WARNING,
        "asyncio": logging.WARNING,
    }
    for logger_name, level in library_loggers.items():
        logging.getLogger(logger_name).setLevel(level)


def get_request_logger(request_id: str) -> logging.LoggerAdapter:
    """
    Get a logger adapter for a specific request.

    Args:
        request_id: The request ID
    Returns:
        Logger adapter with request context
    """
    logger = logging.getLogger("app.request")
    return RequestAdapter(logger, request_id)


class MetricsLogger:
    """
    Logger for application metrics and performance monitoring.

    This class provides methods to log various metrics in a structured format
    that can be easily consumed by monitoring systems.
    """

    def __init__(self):
        """Initialize the metrics logger."""
        self.logger = logging.getLogger("app.metrics")

    def log_request(
        self,
        request_id: str,
        method: str,
        path: str,
        status_code: int,
        duration_ms: float,
        user_agent: Optional[str] = None,
        ip_address: Optional[str] = None,
        extra: Optional[Dict[str, Any]] = None,
    ):
        """
        Log information about an HTTP request.

        Args:
            request_id: Unique request identifier
            method: HTTP method
            path: Request path
            status_code: HTTP status code
            duration_ms: Request duration in milliseconds
            user_agent: User agent string
            ip_address: Client IP address
            extra: Additional data to log
        """
        data = {
            "request_id": request_id,
            "method": method,
            "path": path,
            "status_code": status_code,
            "duration_ms": duration_ms,
        }
        if user_agent:
            data["user_agent"] = user_agent
        if ip_address:
            data["ip_address"] = ip_address
        if extra:
            data.update(extra)
        self.logger.info(
            f"Request {method} {path} completed in {duration_ms:.2f}ms", extra={"extra": data}
        )

    def log_carousel_generation(
        self,
        carousel_id: str,
        num_slides: int,
        duration_ms: float,
        success: bool,
        error: Optional[str] = None,
    ):
        """
        Log carousel generation metrics.

        Args:
            carousel_id: Unique carousel identifier
            num_slides: Number of slides generated
            duration_ms: Generation duration in milliseconds
            success: Whether generation was successful
            error: Error message if generation failed
        """
        data = {
            "carousel_id": carousel_id,
            "num_slides": num_slides,
            "duration_ms": duration_ms,
            "success": success,
        }
        if error:
            data["error"] = error
        status = "succeeded" if success else "failed"
        self.logger.info(
            f"Carousel generation {status} in {duration_ms:.2f}ms for {num_slides} slides",
            extra={"extra": data},
        )

    def log_image_processing(
        self,
        operation: str,
        image_size: tuple,
        duration_ms: float,
        success: bool,
        error: Optional[str] = None,
    ):
        """
        Log image processing metrics.

        Args:
            operation: Image processing operation name
            image_size: Image dimensions (width, height)
            duration_ms: Processing duration in milliseconds
            success: Whether processing was successful
            error: Error message if processing failed
        """
        data = {
            "operation": operation,
            "image_size": f"{image_size[0]}x{image_size[1]}",
            "duration_ms": duration_ms,
            "success": success,
        }
        if error:
            data["error"] = error
        status = "succeeded" if success else "failed"
        self.logger.info(
            f"Image {operation} {status} in {duration_ms:.2f}ms", extra={"extra": data}
        )

    def log_api_rate_limit(
        self,
        endpoint: str,
        client_ip: str,
        request_count: int,
        window_seconds: int,
        limit_exceeded: bool,
    ):
        """
        Log API rate limiting events.

        Args:
            endpoint: API endpoint
            client_ip: Client IP address
            request_count: Number of requests in the time window
            window_seconds: Time window in seconds
            limit_exceeded: Whether the rate limit was exceeded
        """
        data = {
            "endpoint": endpoint,
            "client_ip": client_ip,
            "request_count": request_count,
            "window_seconds": window_seconds,
            "limit_exceeded": limit_exceeded,
        }
        if limit_exceeded:
            self.logger.warning(
                f"Rate limit exceeded for {endpoint} by {client_ip}", extra={"extra": data}
            )
        else:
            self.logger.debug(
                f"Rate limit status for {endpoint}: {request_count}/{window_seconds}s",
                extra={"extra": data},
            )

    def log_system_metrics(
        self,
        cpu_usage: float,
        memory_usage: float,
        disk_usage: float,
        carousel_count: int,
        active_requests: int,
    ):
        """
        Log system resource metrics.

        Args:
            cpu_usage: CPU usage percentage
            memory_usage: Memory usage percentage
            disk_usage: Disk usage percentage
            carousel_count: Number of carousels stored
            active_requests: Number of active requests
        """
        data = {
            "cpu_usage": cpu_usage,
            "memory_usage": memory_usage,
            "disk_usage": disk_usage,
            "carousel_count": carousel_count,
            "active_requests": active_requests,
        }
        self.logger.info(
            f"System metrics: CPU {cpu_usage:.1f}%, Memory {memory_usage:.1f}%, Disk {disk_usage:.1f}%",
            extra={"extra": data},
        )


# Create singleton instances
metrics_logger = MetricsLogger()


def get_metrics_logger() -> MetricsLogger:
    """
    Get the metrics logger instance.

    Returns:
        MetricsLogger instance
    """
    return metrics_logger


# Performance monitoring decorator
def monitor_performance(operation_name: str = None):
    """
    Set up to monitor the performance of a function.

    Args:
        operation_name: Name of the operation being monitored
    Returns:
        Decorated function
    """

    def decorator(func):
        def wrapper(*args, **kwargs):
            # Get operation name from function if not provided
            op_name = operation_name or func.__name__

            # Start timing
            start_time = time.time()

            try:
                # Call the function
                result = func(*args, **kwargs)
                success = True
                error = None
            except Exception as e:
                # Log exception
                success = False
                error = str(e)
                raise
            finally:
                # Calculate duration
                duration_ms = (time.time() - start_time) * 1000

                # Log performance
                logging.getLogger("app.performance").info(
                    f"Operation '{op_name}' {'succeeded' if success else 'failed'} in {duration_ms:.2f}ms",
                    extra={
                        "extra": {
                            "operation": op_name,
                            "duration_ms": duration_ms,
                            "success": success,
                            "error": error,
                        }
                    },
                )

            return result

        return wrapper

    return decorator


# Async version of the performance monitoring decorator
def monitor_performance_async(operation_name: str = None):
    """
    Set up to monitor the performance of an async function.

    Args:
        operation_name: Name of the operation being monitored
    Returns:
        Decorated async function
    """

    def decorator(func):
        async def wrapper(*args, **kwargs):
            # Get operation name from function if not provided
            op_name = operation_name or func.__name__

            # Start timing
            start_time = time.time()

            try:
                # Call the function
                result = await func(*args, **kwargs)
                success = True
                error = None
            except Exception as e:
                # Log exception
                success = False
                error = str(e)
                raise
            finally:
                # Calculate duration
                duration_ms = (time.time() - start_time) * 1000

                # Log performance
                logging.getLogger("app.performance").info(
                    f"Operation '{op_name}' {'succeeded' if success else 'failed'} in {duration_ms:.2f}ms",
                    extra={
                        "extra": {
                            "operation": op_name,
                            "duration_ms": duration_ms,
                            "success": success,
                            "error": error,
                        }
                    },
                )

            return result

        return wrapper

    return decorator
