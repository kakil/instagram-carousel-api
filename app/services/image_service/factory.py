"""
Factory module for image service implementations.

This module provides factory functions for creating image service instances
and handles the selection of the appropriate implementation based on type.
"""
import logging
from enum import Enum
from typing import Any, Dict, Optional

from app.services.image_service.base_image_service import BaseImageService
from app.services.image_service.enhanced_image_service import EnhancedImageService
from app.services.image_service.standard_image_service import StandardImageService

logger = logging.getLogger(__name__)


class ImageServiceType(Enum):
    """Enum defining available image service implementations."""

    STANDARD = "standard"
    ENHANCED = "enhanced"


def get_image_service(
    service_type: str = ImageServiceType.ENHANCED.value,
    settings: Optional[Dict[str, Any]] = None,
) -> BaseImageService:
    """
    Get the appropriate image service implementation.

    Args:
        service_type: The type of image service to retrieve (standard or enhanced)
        settings: Optional dictionary of settings to pass to the image service

    Returns:
        An instance of BaseImageService implementation

    Raises:
        ValueError: If an invalid service_type is provided
    """
    settings = settings or {}

    if service_type == ImageServiceType.STANDARD.value:
        logger.info("Creating StandardImageService instance")
        return StandardImageService(settings)
    elif service_type == ImageServiceType.ENHANCED.value:
        logger.info("Creating EnhancedImageService instance")
        return EnhancedImageService(settings)
    else:
        available_types = [t.value for t in ImageServiceType]
        raise ValueError(
            f"Invalid image service type: {service_type}. Available types: "
            f"{', '.join(available_types)}"
        )


# For backward compatibility with existing code
def get_default_image_service(settings: Optional[Dict[str, Any]] = None) -> BaseImageService:
    """
    Get the default image service implementation (currently Enhanced).

    This function helps maintain backward compatibility with existing code.

    Args:
        settings: Optional dictionary of settings to pass to the image service

    Returns:
        The default BaseImageService implementation
    """
    return get_image_service(ImageServiceType.ENHANCED.value, settings)
