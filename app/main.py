"""
Main module for the Instagram Carousel Generator API.

This module provides the FastAPI application setup and server entry point.
"""
import logging
import os
import time
import uuid
from contextlib import asynccontextmanager
from datetime import datetime

import psutil
import uvicorn
from fastapi import Depends, FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import RedirectResponse
from fastapi.staticfiles import StaticFiles

from app.api.security import get_api_key, rate_limit
from app.core.config import settings
from app.core.logging import configure_logging, get_request_logger, metrics_logger
from app.services.storage_service import StorageService

# Configure structured logging
configure_logging()

# Get a logger for this module
logger = logging.getLogger(__name__)

# Initialize storage service
storage_service = StorageService()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Lifecycle hooks for the FastAPI application.

    Args:
        app: The FastAPI application
    """
    # Startup logic
    logger.info(
        "Starting Instagram Carousel Generator API",
        extra={
            "extra": {
                "version": "1.0.0",
                "environment": "production" if settings.PRODUCTION else "development",
            }
        },
    )

    # Initialize the dependency injection system
    from app.core.services_setup import register_services

    register_services()
    logger.info("Service registry initialized")

    # Clean up old files
    storage_service.cleanup_old_files()

    # Start periodic system metrics reporting if enabled
    if settings.ENABLE_SYSTEM_METRICS:
        logger.info("System metrics reporting enabled")
        # Set up periodic system metrics reporting
        # This would typically be done with a background task or separate process
        # For simplicity, we'll just log once at startup
        log_system_metrics()

    yield  # This is where the app runs

    # Shutdown logic
    logger.info("Shutting down Instagram Carousel Generator API")


def create_app() -> FastAPI:
    """
    Create and configure the FastAPI application.

    Returns:
        Configured FastAPI application
    """
    # Initialize the dependency injection system
    from app.core.services_setup import register_services

    register_services()

    # Create the FastAPI app with proper configuration
    app = FastAPI(
        title=settings.PROJECT_NAME,
        description="""
        API for generating Instagram carousel images with consistent styling.

        ## API Versioning

        This API uses URL-based versioning (e.g., `/api/v1/...`).
        Always include the version in your API requests to ensure compatibility.

        - Current version: v1
        - For more information about versioning, see the `/api-info` endpoint or visit our [API Versioning Guide](/docs#section/Versioning).

        ## Dependency Injection

        This API uses dependency injection for service management, which makes components more
        modular, testable, and extensible. See our dependency injection guide in the documentation
        for more details.
        """,
        version="1.0.0",
        lifespan=lifespan,
    )

    # Configure CORS with more restrictive settings in production
    # In production, restrict origins to your specific domains
    origins = settings.ALLOW_ORIGINS
    if settings.PRODUCTION and origins == ["*"]:
        logger.warning("Using wildcard CORS origin in production. Consider restricting origins.")

    app.add_middleware(
        CORSMiddleware,
        allow_origins=origins,
        allow_credentials=settings.ALLOW_CREDENTIALS,
        allow_methods=settings.ALLOW_METHODS,
        allow_headers=settings.ALLOW_HEADERS,
    )

    # Add the API version middleware
    from app.api.middleware import version_middleware

    @app.middleware("http")
    async def api_version_middleware(request: Request, call_next):
        """Middleware for managing API versioning notices."""
        return await version_middleware(request, call_next)

    # Middleware to ensure UTF-8 encoding for all responses
    @app.middleware("http")
    async def add_encoding_header(request: Request, call_next):
        response = await call_next(request)
        # Only set Content-Type for JSON responses to avoid interfering with other response types
        if response.headers.get("Content-Type", "").startswith("application/json"):
            response.headers["Content-Type"] = "application/json; charset=utf-8"
        return response

    # Enhanced request logging middleware with metrics
    @app.middleware("http")
    async def enhanced_request_logging(request: Request, call_next):
        # Generate a unique request ID
        request_id = str(uuid.uuid4())

        # Add request ID to request state for access in route handlers
        request.state.request_id = request_id

        # Get client info safely
        client_host = request.client.host if request.client else "unknown"

        # Create request-specific logger
        request_logger = get_request_logger(request_id)

        # Log request start
        start_time = time.time()
        request_logger.info(
            f"Request started: {request.method} {request.url.path}",
            extra={
                "request_method": request.method,
                "request_path": request.url.path,
                "client_ip": client_host,
            },
        )

        # Process the request
        try:
            response = await call_next(request)
            status_code = response.status_code
        except Exception as e:
            # Log exceptions
            request_logger.error(f"Request failed with exception: {str(e)}", exc_info=True)
            raise
        finally:
            # Calculate processing time
            process_time = time.time() - start_time
            duration_ms = process_time * 1000

            # Determine response category
            response_category = get_response_category(status_code)

            # Log request completion
            request_logger.info(
                f"Request completed: {request.method} {request.url.path} - {status_code} {response_category} in {duration_ms:.2f}ms",
                extra={
                    "status_code": status_code,
                    "duration_ms": duration_ms,
                    "response_category": response_category,
                },
            )

            # Log metrics
            metrics_logger.log_request(
                request_id=request_id,
                method=request.method,
                path=request.url.path,
                status_code=status_code,
                duration_ms=duration_ms,
                ip_address=client_host,
                user_agent=request.headers.get("user-agent"),
            )

        # Add request ID and timing headers
        if hasattr(response, "headers"):
            response.headers["X-Request-ID"] = request_id
            response.headers["X-Process-Time"] = f"{process_time:.6f}"

        return response

    # Mount static directories
    app.mount("/static", StaticFiles(directory=str(settings.STATIC_DIR)), name="static")

    # Health check endpoint (no authentication required)
    @app.get("/health", tags=["health"])
    async def health_check(request: Request):
        """Enhanced health check endpoint with system metrics."""
        # Get basic health data
        health_data = {
            "status": "healthy",
            "timestamp": datetime.now().isoformat(),
            "version": "1.0.0",
            "api_version": "v1",
            "request_id": getattr(request.state, "request_id", None),
        }

        # Add system metrics if enabled
        if settings.ENABLE_SYSTEM_METRICS:
            try:
                health_data.update(
                    {
                        "system": {
                            "cpu_usage": psutil.cpu_percent(),
                            "memory_usage": psutil.virtual_memory().percent,
                            "disk_usage": psutil.disk_usage("/").percent,
                        }
                    }
                )
            except Exception as e:
                logger.warning(f"Failed to collect system metrics: {str(e)}")

        return health_data

    @app.get("/api-info", tags=["versioning"])
    async def api_info():
        """Get API version information."""
        from app.api.middleware import get_all_versions, get_latest_version

        return {
            "api_name": settings.PROJECT_NAME,
            "api_version": "1.0.0",
            "available_versions": get_all_versions(),
            "latest_version": get_latest_version(),
            "documentation_url": f"{settings.PUBLIC_BASE_URL}/docs",
        }

    # Metrics endpoint for monitoring applications
    @app.get("/metrics", tags=["monitoring"])
    async def metrics(request: Request):
        """Get application metrics for monitoring."""
        # This could be expanded to provide Prometheus-compatible metrics
        # or other formats as needed
        try:
            # Get carousel count
            carousel_count = count_carousels()

            metrics_data = {
                "timestamp": datetime.now().isoformat(),
                "uptime": get_uptime(),
                "requests": {
                    "active": getattr(app.state, "active_requests", 0),
                    "total": getattr(app.state, "total_requests", 0),
                    "errors": getattr(app.state, "error_count", 0),
                },
                "carousels": {
                    "count": carousel_count,
                    "generated_today": getattr(app.state, "carousels_today", 0),
                },
                "system": {
                    "cpu_usage": psutil.cpu_percent(),
                    "memory_usage": psutil.virtual_memory().percent,
                    "disk_usage": psutil.disk_usage("/").percent,
                },
            }

            return metrics_data
        except Exception as e:
            logger.error(f"Error generating metrics: {str(e)}")
            return {
                "status": "error",
                "message": "Failed to generate metrics",
                "timestamp": datetime.now().isoformat(),
            }

    # Redirect root to docs
    @app.get("/", include_in_schema=False)
    async def root():
        return RedirectResponse(url="/docs")

    # Include the versioned API router
    from app.api.router import api_router

    # Apply API key security to all API endpoints
    # Public endpoints like health check are defined directly in this file
    app.include_router(
        api_router,
        prefix=settings.API_PREFIX,  # Only use the prefix without version
        dependencies=[Depends(get_api_key), Depends(rate_limit())],
    )

    return app


def get_response_category(status_code: int) -> str:
    """
    Get a category name for a response status code.

    Args:
        status_code: HTTP status code

    Returns:
        Category name
    """
    if 100 <= status_code < 200:
        return "informational"
    elif 200 <= status_code < 300:
        return "success"
    elif 300 <= status_code < 400:
        return "redirect"
    elif 400 <= status_code < 500:
        return "client_error"
    elif 500 <= status_code < 600:
        return "server_error"
    else:
        return "unknown"


def count_carousels() -> int:
    """
    Count the number of carousel directories in the temp directory.

    Returns:
        Number of carousel directories
    """
    try:
        # Get the temp directory
        temp_dir = storage_service.temp_dir

        # Count directories that look like carousel IDs (excluding hidden directories)
        count = sum(
            1
            for item in os.listdir(temp_dir)
            if os.path.isdir(os.path.join(temp_dir, item)) and not item.startswith(".")
        )

        return count
    except Exception as e:
        logger.error(f"Error counting carousels: {str(e)}")
        return 0


def get_uptime() -> float:
    """
    Get the application uptime in seconds.

    Returns:
        Uptime in seconds
    """
    # This is a simplified version that only works for the current process
    # For a production system, you might want to track this differently
    try:
        process = psutil.Process(os.getpid())
        return time.time() - process.create_time()
    except Exception as e:
        logger.error(f"Error getting uptime: {str(e)}")
        return 0.0


def log_system_metrics():
    """Log system resource metrics."""
    try:
        # Get system metrics
        cpu_usage = psutil.cpu_percent()
        memory_usage = psutil.virtual_memory().percent
        disk_usage = psutil.disk_usage("/").percent
        carousel_count = count_carousels()

        # Log metrics
        metrics_logger.log_system_metrics(
            cpu_usage=cpu_usage,
            memory_usage=memory_usage,
            disk_usage=disk_usage,
            carousel_count=carousel_count,
            active_requests=0,  # This would be tracked in a real application
        )
    except Exception as e:
        logger.error(f"Failed to log system metrics: {str(e)}")


def run_app():
    """Run the FastAPI application with uvicorn."""
    uvicorn.run(
        "app.main:create_app",
        host=settings.HOST,
        port=settings.PORT,
        reload=settings.DEBUG,
        factory=True,
    )


# For direct execution
if __name__ == "__main__":
    run_app()
