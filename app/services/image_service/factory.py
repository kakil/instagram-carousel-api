from typing import Dict, Any, Optional
import logging
from enum import Enum

from app.services.image_service.base_image_service import BaseImageService
from app.services.image_service.standard_image_service import StandardImageService
from app.services.image_service.enhanced_image_service import EnhancedImageService

logger = logging.getLogger(__name__)


class ImageServiceType(Enum):
    """Enum defining available image service implementations."""
    STANDARD = "standard"
    ENHANCED = "enhanced"


def get_image_service(service_type: str = ImageServiceType.ENHANCED.value,
                      settings: Optional[
                          Dict[str, Any]] = None) -> BaseImageService:
    """
    Factory function to get the appropriate image service implementation.

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
            f"Invalid image service type: {service_type}. Available types: {', '.join(available_types)}")


# For backward compatibility with existing code
def get_default_image_service(
        settings: Optional[Dict[str, Any]] = None) -> BaseImageService:
    """
    Returns the default image service implementation (currently Enhanced).
    This function helps maintain backward compatibility with existing code.

    Args:
        settings: Optional dictionary of settings to pass to the image service

    Returns:
        The default BaseImageService implementation
    """
    return get_image_service(ImageServiceType.ENHANCED.value, settings)