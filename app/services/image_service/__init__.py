"""
Image Service Module for Instagram Carousel Generator.

This module provides classes and utilities for generating images for
Instagram carousels.
It offers different implementations with varying levels of features
and error handling.
Classes:
    BaseImageService: Abstract base class that defines the interface
    StandardImageService: Basic implementation with core functionality
    EnhancedImageService: Advanced implementation with improved error
    handling and text rendering
Functions:
    get_image_service: Factory function to create the appropriate
    service instance
    get_default_image_service: Returns the default service
    (for backward compatibility)
"""
from .base_image_service import (
    BaseImageService,
    FontLoadError,
    ImageCreationError,
    ImageServiceError,
    TextRenderingError,
)
from .enhanced_image_service import EnhancedImageService
from .factory import ImageServiceType, get_default_image_service, get_image_service
from .standard_image_service import StandardImageService

# For backward compatibility with existing code
# This allows current production code to continue working with minimal changes
default_service = get_default_image_service()
create_carousel_images = default_service.create_carousel_images
create_slide_image = default_service.create_slide_image
create_gradient_text = default_service.create_gradient_text
create_error_slide = default_service.create_error_slide
sanitize_text = default_service.sanitize_text

# Export the factory functions and enums at the module level
__all__ = [
    # Classes
    "BaseImageService",
    "StandardImageService",
    "EnhancedImageService",
    # Factory functions
    "get_image_service",
    "get_default_image_service",
    # Enums
    "ImageServiceType",
    # Exceptions
    "ImageServiceError",
    "ImageCreationError",
    "FontLoadError",
    "TextRenderingError",
    # Legacy function exports for backward compatibility
    "create_carousel_images",
    "create_slide_image",
    "create_gradient_text",
    "create_error_slide",
    "sanitize_text",
]
