"""
Service setup for the Instagram Carousel Generator.

This module configures all required services in the service provider,
establishing proper dependency injection for the application.
"""

import logging
from typing import Dict, Any, Optional, Type, TypeVar

from app.core.service_provider import get_service_provider, ServiceProvider
from app.core.config import settings

# Import service interfaces and implementations
from app.services.image_service import (
    BaseImageService,
    get_image_service,
    ImageServiceType
)
from app.services.storage_service import StorageService, storage_service

# Set up logging
logger = logging.getLogger(__name__)

# Type variable for generic service types
T = TypeVar('T')


def register_services():
    """
    Register all application services with the service provider.
    This function should be called during application startup.
    """
    provider = get_service_provider()
    logger.info("Registering application services...")

    # Register Storage Service
    provider.register_instance(StorageService, storage_service)

    # Register Image Service configurations
    register_image_services(provider)

    logger.info("Service registration complete")


def register_image_services(provider: ServiceProvider):
    """
    Register different image service implementations.

    Args:
        provider: The service provider to register with
    """
    # Get default image service settings
    image_settings = get_image_service_settings()

    # Register Standard Image Service with a specific key
    provider.register(
        BaseImageService,
        lambda: get_image_service(ImageServiceType.STANDARD.value,
                                  image_settings),
        singleton=True
    )
    provider._services[BaseImageService]["StandardImageService"] = provider._services[BaseImageService][BaseImageService.__name__]

    # Register Enhanced Image Service with a specific key
    provider.register(
        BaseImageService,
        lambda: get_image_service(ImageServiceType.ENHANCED.value,
                                  image_settings),
        singleton=True
    )
    provider._services[BaseImageService]["EnhancedImageService"] = provider._services[BaseImageService][BaseImageService.__name__]

    logger.info("Image services registered")


def get_image_service_settings() -> Dict[str, Any]:
    """
    Create a settings dictionary for image services.

    Returns:
        Dict[str, Any]: Settings for image services
    """
    return {
        'width': settings.DEFAULT_WIDTH,
        'height': settings.DEFAULT_HEIGHT,
        'bg_color': settings.DEFAULT_BG_COLOR,
        'title_font': settings.DEFAULT_FONT_BOLD,
        'text_font': settings.DEFAULT_FONT,
        'nav_font': settings.DEFAULT_FONT
    }


def get_service(service_type: Type[T], key: Optional[str] = None) -> T:
    """
    Get a service from the service provider.
    This is a convenience function that can be used by FastAPI dependencies.

    Args:
        service_type: The type of service to get
        key: Optional key for when multiple implementations exist

    Returns:
        An instance of the requested service
    """
    provider = get_service_provider()
    return provider.get(service_type, key)