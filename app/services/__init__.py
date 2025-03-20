"""
Services module for the Instagram Carousel Generator.

This module contains various services used by the application:
- image_service: Handles the creation of carousel images
- storage_service: Manages temporary file storage and retrieval
"""

# Make the image_service module directly importable from app.services
from app.services.image_service import (
    get_image_service,
    get_default_image_service,
    ImageServiceType,
    create_carousel_images,
    create_slide_image,
    create_gradient_text,
    create_error_slide,
    sanitize_text
)

# Import the storage service for easy access
# This assumes storage_service.py is in the same directory
from app.services.storage_service import (
    save_carousel_images,
    get_file_path,
    get_content_type,
    cleanup_old_files,
    schedule_cleanup
)

__all__ = [
    # Image service exports
    'get_image_service',
    'get_default_image_service',
    'ImageServiceType',
    'create_carousel_images',
    'create_slide_image',
    'create_gradient_text',
    'create_error_slide',
    'sanitize_text',

    # Storage service exports
    'save_carousel_images',
    'get_file_path',
    'get_content_type',
    'cleanup_old_files',
    'schedule_cleanup'
]