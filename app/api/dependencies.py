"""
Centralized dependencies for the Instagram Carousel Generator API.

This module provides dependency injection functions that can be used with FastAPI's
dependency injection system. Centralizing dependencies makes them easier to mock
for testing and replace for different environments.
"""
import logging
import time

from fastapi import BackgroundTasks, Request

from app.api.security import get_api_key, rate_limit
from app.core.config import settings
from app.core.services_setup import get_service, register_services
from app.services.image_service import BaseImageService
from app.services.storage_service import StorageService

# Set up logging
logger = logging.getLogger(__name__)


# Ensure services are registered
register_services()


# Rate limiting dependencies
def get_standard_rate_limit():
    """
    Return standard rate limit dependency for general endpoints.

    Returns:
        Dependency function for standard rate limiting
    """
    return rate_limit(
        max_requests=settings.RATE_LIMIT_MAX_REQUESTS,
        window_seconds=settings.RATE_LIMIT_WINDOW_SECONDS,
    )


def get_heavy_rate_limit():
    """
    Stricter rate limit for resource-intensive endpoints.

    Returns:
        Dependency function for heavier rate limiting
    """
    return rate_limit(
        max_requests=20,  # Lower limit for resource-intensive operations
        window_seconds=60,
    )


# Authentication dependencies
def get_api_key_dependency():
    """
    Dependency for API key authentication.

    Returns:
        API key dependency function
    """
    return get_api_key


# Service dependencies using service provider
def get_storage_service() -> StorageService:
    """
    Provide the storage service instance from the service provider.

    Returns:
        StorageService: Instance of the storage service
    """
    return get_service(StorageService)


def get_standard_image_service() -> BaseImageService:
    """
    Provide a standard image service instance from the service provider.

    This uses the registered standard image service from the service provider.

    Returns:
        BaseImageService: Standard image service implementation
    """
    return get_service(BaseImageService, key="StandardImageService")


def get_enhanced_image_service() -> BaseImageService:
    """
    Provide an enhanced image service instance from the service provider.

    This uses the registered enhanced image service from the service provider.

    Returns:
        BaseImageService: Enhanced image service implementation
    """
    return get_service(BaseImageService, key="EnhancedImageService")


# API versioning dependencies
def set_api_version(request: Request, version: str) -> None:
    """
    Set API version in request state.

    Args:
        request: The FastAPI request object
        version: API version string (e.g., "v1")

    Returns:
        None
    """
    request.state.api_version = version
    logger.debug(f"Request to API version: {version}")
    return None


def set_v1_api_version(request: Request) -> None:
    """
    Set API version to v1 in request state.

    This is a convenience function for v1 API routes.

    Args:
        request: The FastAPI request object

    Returns:
        None
    """
    return set_api_version(request, "v1")


# Request tracking
async def log_request_info(request: Request) -> float:
    """
    Log request information and return start time.

    Args:
        request: The FastAPI request object

    Returns:
        float: Start time of the request
    """
    start_time = time.time()
    client_host = request.client.host if request.client else "unknown"
    logger.info(f"Request from {client_host} - {request.method} {request.url.path}")
    return start_time


# Cleanup dependencies
def get_background_tasks(background_tasks: BackgroundTasks) -> BackgroundTasks:
    """
    Provide background tasks object.

    This is mainly for clarity and future extensibility.

    Args:
        background_tasks: FastAPI's BackgroundTasks object

    Returns:
        BackgroundTasks: The same object, passed through
    """
    return background_tasks


def cleanup_temp_files(carousel_id: str):
    """
    Schedule cleanup for temporary files.

    Args:
        carousel_id: ID of the carousel to clean up
    """
    logger.info(f"Scheduled cleanup for carousel {carousel_id}")
    storage_service = get_storage_service()
    # Get the carousel directory
    carousel_dir = storage_service.temp_dir / carousel_id
    logger.info(f"Scheduling cleanup for directory: {carousel_dir}")
    # This function is intended to be used with background_tasks.add_task
