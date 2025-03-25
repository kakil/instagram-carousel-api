"""
Monitoring middleware and utilities for the Instagram Carousel Generator API.

This module provides middleware and utility functions for monitoring
API performance, tracking errors, and collecting metrics.
"""
import logging
import time
import uuid
from typing import Any, Awaitable, Callable, Dict, List

from fastapi import Request, Response

from app.core.logging import get_request_logger, metrics_logger

# Set up logging
logger = logging.getLogger(__name__)


# Metrics tracker class
class APIMetricsTracker:
    """
    Tracker for API metrics.

    This class tracks API metrics like request counts, response times,
    error rates, and carousel generation statistics.
    """

    def __init__(self):
        """Initialize the API metrics tracker."""
        # Endpoint metrics
        self.endpoint_metrics: Dict[str, Dict[str, Any]] = {}
        # Overall metrics
        self.total_requests = 0
        self.error_count = 0
        self.successful_requests = 0
        # Carousel metrics
        self.total_carousels_generated = 0
        self.carousel_generation_times: List[float] = []
        # Response time metrics
        self.response_times: Dict[str, List[float]] = {}

    def track_request(
        self,
        endpoint: str,
        method: str,
        duration_ms: float,
        status_code: int,
        is_error: bool = False,
    ):
        """
        Track metrics for an API request.

        Args:
            endpoint: API endpoint path
            method: HTTP method
            duration_ms: Request duration in milliseconds
            status_code: HTTP status code
            is_error: Whether the request resulted in an error
        """
        # Create endpoint key
        endpoint_key = f"{method}:{endpoint}"
        # Initialize endpoint metrics if not exists
        if endpoint_key not in self.endpoint_metrics:
            self.endpoint_metrics[endpoint_key] = {
                "count": 0,
                "errors": 0,
                "total_duration_ms": 0,
                "min_duration_ms": float("inf"),
                "max_duration_ms": 0,
                "status_codes": {},
            }
        # Update endpoint metrics
        metrics = self.endpoint_metrics[endpoint_key]
        metrics["count"] += 1
        metrics["total_duration_ms"] += duration_ms
        metrics["min_duration_ms"] = min(metrics["min_duration_ms"], duration_ms)
        metrics["max_duration_ms"] = max(metrics["max_duration_ms"], duration_ms)
        # Update status code count
        status_str = str(status_code)
        if status_str not in metrics["status_codes"]:
            metrics["status_codes"][status_str] = 0
        metrics["status_codes"][status_str] += 1
        # Track errors
        if is_error:
            metrics["errors"] += 1
            self.error_count += 1
        # Update overall metrics
        self.total_requests += 1
        self.successful_requests += 0 if is_error else 1
        # Update response time metrics
        if endpoint not in self.response_times:
            self.response_times[endpoint] = []
        self.response_times[endpoint].append(duration_ms)
        # Keep only the last 1000 response times to avoid memory issues
        if len(self.response_times[endpoint]) > 1000:
            self.response_times[endpoint] = self.response_times[endpoint][-1000:]

    def track_carousel_generation(
        self, carousel_id: str, num_slides: int, duration_ms: float, success: bool
    ):
        """
        Track metrics for carousel generation.

        Args:
            carousel_id: Unique carousel identifier
            num_slides: Number of slides generated
            duration_ms: Generation duration in milliseconds
            success: Whether generation was successful
        """
        # Update carousel metrics
        self.total_carousels_generated += 1
        self.carousel_generation_times.append(duration_ms)
        # Keep only the last 1000 generation times to avoid memory issues
        if len(self.carousel_generation_times) > 1000:
            self.carousel_generation_times = self.carousel_generation_times[-1000:]

    def get_metrics(self) -> Dict[str, Any]:
        """
        Get current metrics.

        Returns:
            Dictionary of metrics
        """
        # Calculate average response time
        avg_response_time = 0
        if self.total_requests > 0:
            avg_response_time = (
                sum(metrics["total_duration_ms"] for metrics in self.endpoint_metrics.values())
                / self.total_requests
            )
        # Calculate average carousel generation time
        avg_carousel_time = 0
        if self.carousel_generation_times:
            avg_carousel_time = sum(self.carousel_generation_times) / len(
                self.carousel_generation_times
            )
        # Calculate error rate
        error_rate = 0
        if self.total_requests > 0:
            error_rate = (self.error_count / self.total_requests) * 100
        # Calculate endpoint-specific metrics
        endpoint_stats = {}
        for endpoint, metrics in self.endpoint_metrics.items():
            if metrics["count"] > 0:
                avg_time = metrics["total_duration_ms"] / metrics["count"]
                error_rate_endpoint = (metrics["errors"] / metrics["count"]) * 100
                endpoint_stats[endpoint] = {
                    "count": metrics["count"],
                    "error_count": metrics["errors"],
                    "error_rate": error_rate_endpoint,
                    "avg_duration_ms": avg_time,
                    "min_duration_ms": metrics["min_duration_ms"],
                    "max_duration_ms": metrics["max_duration_ms"],
                    "status_codes": metrics["status_codes"],
                }
        # Return combined metrics
        return {
            "requests": {
                "total": self.total_requests,
                "successful": self.successful_requests,
                "errors": self.error_count,
                "error_rate": error_rate,
                "avg_response_time_ms": avg_response_time,
            },
            "carousels": {
                "total_generated": self.total_carousels_generated,
                "avg_generation_time_ms": avg_carousel_time,
            },
            "endpoints": endpoint_stats,
        }


# Create a singleton instance
metrics_tracker = APIMetricsTracker()


class MonitoringMiddleware:
    """Middleware for monitoring API requests and collecting metrics."""

    def __init__(
        self,
        app: Any,
        exclude_paths: List[str] = None,
    ):
        """
        Initialize the monitoring middleware.

        Args:
            app: FastAPI application
            exclude_paths: Paths to exclude from monitoring
        """
        self.app = app
        self.exclude_paths = exclude_paths or [
            "/health",
            "/metrics",
            "/docs",
            "/redoc",
            "/openapi.json",
        ]

    async def __call__(self, request: Request, call_next: Callable[[Request], Awaitable[Response]]):
        """
        Process the request and collect metrics.

        Args:
            request: FastAPI request object
            call_next: Next middleware or endpoint handler

        Returns:
            Response from the next middleware or endpoint handler
        """
        # Skip monitoring for excluded paths
        path = request.url.path
        if any(path.startswith(excluded) for excluded in self.exclude_paths):
            return await call_next(request)

        # Generate a unique request ID if not already present
        request_id = getattr(request.state, "request_id", str(uuid.uuid4()))
        request.state.request_id = request_id

        # Get endpoint path
        endpoint = path

        # Start timer and create request logger
        start_time = time.time()
        request_logger = get_request_logger(request_id)

        # Track request
        request_logger.info(
            f"Request started: {request.method} {endpoint}",
            extra={
                "method": request.method,
                "endpoint": endpoint,
                "client_ip": request.client.host if request.client else "unknown",
                "user_agent": request.headers.get("user-agent", "unknown"),
            },
        )

        # Process request
        try:
            response = await call_next(request)
            status_code = response.status_code
            is_error = status_code >= 400

        except Exception as e:
            # Log exception
            request_logger.exception(f"Exception during request processing: {str(e)}")

            # Re-raise to let FastAPI handle the exception
            raise

        finally:
            # Calculate duration
            duration_ms = (time.time() - start_time) * 1000

            # Get status code (default to 500 if not set)
            status_code = getattr(response, "status_code", 500)
            is_error = status_code >= 400

            # Track metrics
            metrics_tracker.track_request(
                endpoint=endpoint,
                method=request.method,
                duration_ms=duration_ms,
                status_code=status_code,
                is_error=is_error,
            )

            # Log request completion
            log_level = logging.WARNING if is_error else logging.INFO
            request_logger.log(
                log_level,
                f"Request completed: {request.method} {endpoint} - {status_code} in {duration_ms:.2f}ms",
                extra={
                    "status_code": status_code,
                    "duration_ms": duration_ms,
                    "is_error": is_error,
                },
            )

            # Add metrics to metrics logger
            metrics_logger.log_request(
                request_id=request_id,
                method=request.method,
                path=endpoint,
                status_code=status_code,
                duration_ms=duration_ms,
                ip_address=request.client.host if request.client else "unknown",
                user_agent=request.headers.get("user-agent"),
            )

            # Add headers to the response
            if hasattr(response, "headers"):
                response.headers["X-Request-ID"] = request_id
                response.headers["X-Response-Time"] = f"{duration_ms:.2f}ms"

        return response


def get_metrics() -> Dict[str, Any]:
    """
    Get current API metrics.

    Returns:
        Dictionary of metrics
    """
    return metrics_tracker.get_metrics()


def track_carousel_generation(carousel_id: str, num_slides: int, duration_ms: float, success: bool):
    """
    Track metrics for carousel generation.

    Args:
        carousel_id: Unique carousel identifier
        num_slides: Number of slides generated
        duration_ms: Generation duration in milliseconds
        success: Whether generation was successful
    """
    # Update metrics tracker
    metrics_tracker.track_carousel_generation(
        carousel_id=carousel_id, num_slides=num_slides, duration_ms=duration_ms, success=success
    )

    # Log to metrics logger
    metrics_logger.log_carousel_generation(
        carousel_id=carousel_id,
        num_slides=num_slides,
        duration_ms=duration_ms,
        success=success,
        error=None if success else "Generation failed",
    )
