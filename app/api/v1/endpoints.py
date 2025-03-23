"""
API endpoints for version 1 of the Instagram Carousel Generator.

This module defines the v1 endpoints for carousel generation and management.
"""

from fastapi import APIRouter, HTTPException, Request, BackgroundTasks, Depends
from fastapi.responses import FileResponse
import uuid
import os
import logging
import time
from typing import Dict, Any, List, Optional
import traceback
from pathlib import Path

# Import the service and model dependencies
from app.services.image_service import get_image_service, ImageServiceType
from app.services import storage_service
from app.core.config import settings
from app.api.security import validate_file_access, rate_limit
from app.api.v1.models import (
    SlideContent,
    CarouselRequest,
    CarouselResponse,
    CarouselResponseWithUrls,
)

# Set up logging
logger = logging.getLogger(__name__)

# Create a router for the v1 endpoints
router = APIRouter()


# Add request logging middleware
async def log_request_info(request: Request):
    """Log basic request information"""
    start_time = time.time()
    client_host = request.client.host if request.client else "unknown"
    logger.info(
        f"Request from {client_host} - {request.method} {request.url.path}"
    )
    return start_time


# Add background task for cleanup
def cleanup_temp_files(carousel_id: str):
    """Cleanup any temporary files created during carousel generation"""
    # This could be expanded to clean up any files stored temporarily
    logger.info(f"Cleaning up temporary files for carousel {carousel_id}")


# Create a dependency to provide the image service
def get_enhanced_image_service():
    """
    Dependency that provides the enhanced image service.
    This allows for easy testing and mocking.
    """
    service_settings = {
        'width': settings.DEFAULT_WIDTH,
        'height': settings.DEFAULT_HEIGHT,
        'bg_color': settings.DEFAULT_BG_COLOR,
        'title_font': settings.DEFAULT_FONT_BOLD,
        'text_font': settings.DEFAULT_FONT,
        'nav_font': settings.DEFAULT_FONT
    }
    return get_image_service(ImageServiceType.ENHANCED.value, service_settings)


# Apply more aggressive rate limiting to generation endpoints
heavy_rate_limit = rate_limit(max_requests=20, window_seconds=60)


@router.post("/generate-carousel", response_model=CarouselResponse,
             tags=["carousel"])
async def generate_carousel(
        request: CarouselRequest,
        background_tasks: BackgroundTasks,
        req: Request,
        image_service=Depends(get_enhanced_image_service),
        # Apply more strict rate limiting for resource-intensive endpoints
        _: None = Depends(heavy_rate_limit)
):
    """Generate carousel images from provided text content"""
    start_time = await log_request_info(req)
    warnings = []

    try:
        # Create a unique ID for this carousel
        carousel_id = str(uuid.uuid4())[:8]
        logger.info(f"Starting carousel generation for ID: {carousel_id}")

        # Check for potentially problematic characters in text
        for i, slide in enumerate(request.slides):
            if any(ord(c) > 127 for c in slide.text):
                warnings.append(
                    f"Slide {i + 1} contains non-ASCII characters which may not render correctly"
                )
                logger.warning(
                    f"Non-ASCII characters detected in slide {i + 1}"
                )

        # Default settings if none provided
        service_settings = request.settings or {
            'width': settings.DEFAULT_WIDTH,
            'height': settings.DEFAULT_HEIGHT,
            'bg_color': settings.DEFAULT_BG_COLOR,
            'title_font': settings.DEFAULT_FONT_BOLD,
            'text_font': settings.DEFAULT_FONT,
            'nav_font': settings.DEFAULT_FONT
        }

        # Generate carousel images using the image service
        result = image_service.create_carousel_images(
            request.carousel_title,
            [{"text": slide.text} for slide in request.slides],
            carousel_id,
            request.include_logo,
            request.logo_path
        )

        # Schedule cleanup
        background_tasks.add_task(cleanup_temp_files, carousel_id)

        # Calculate processing time
        processing_time = round(time.time() - start_time, 2)
        logger.info(f"Carousel {carousel_id} generated in {processing_time}s")

        return {
            "status": "success",
            "carousel_id": carousel_id,
            "slides": result,
            "processing_time": processing_time,
            "warnings": warnings
        }

    except Exception as e:
        # Handle general errors
        logger.error(f"Unexpected error: {str(e)}")
        logger.error(traceback.format_exc())

        error_message = str(e)
        if "codec can't encode character" in error_message:
            error_message = f"Unicode character issue: {error_message}. Try removing special characters from your text."

        raise HTTPException(status_code=500,
                            detail=f"Error generating carousel: {error_message}")


@router.post("/generate-carousel-with-urls",
             response_model=CarouselResponseWithUrls,
             tags=["carousel"])
async def generate_carousel_with_urls(
        request: CarouselRequest,
        background_tasks: BackgroundTasks,
        req: Request,
        image_service=Depends(get_enhanced_image_service),
        # Apply more strict rate limiting for resource-intensive endpoints
        _: None = Depends(heavy_rate_limit)
):
    """Generate carousel images and return URLs for temporary access"""
    try:
        # Create a unique ID for this carousel
        carousel_id = str(uuid.uuid4())[:8]
        logger.info(
            f"Starting carousel generation with URLs for ID: {carousel_id}"
        )

        # Generate carousel images
        result = image_service.create_carousel_images(
            request.carousel_title,
            [{"text": slide.text} for slide in request.slides],
            carousel_id,
            request.include_logo,
            request.logo_path
        )

        # Determine base URL for public access - use configuration
        base_url = settings.PUBLIC_BASE_URL

        # Save images and get public URLs
        public_urls = storage_service.save_carousel_images(
            carousel_id,
            result,
            base_url
        )

        # Schedule cleanup of these files after configured lifetime
        carousel_dir = storage_service.temp_dir / carousel_id
        storage_service.schedule_cleanup(
            background_tasks,
            carousel_dir,
            hours=settings.TEMP_FILE_LIFETIME_HOURS
        )

        return {
            "status": "success",
            "carousel_id": carousel_id,
            "slides": result,
            "public_urls": public_urls
        }

    except Exception as e:
        logger.error(f"Error generating carousel with URLs: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Error generating carousel: {str(e)}"
        )


@router.get("/temp/{carousel_id}/{filename}", tags=["files"])
async def get_temp_file(carousel_id: str, filename: str):
    """Serve a temporary file with proper content type"""
    # Validate file access parameters to prevent directory traversal
    validate_file_access(carousel_id, filename)

    # Log request info
    logger.info(f"File request: carousel_id={carousel_id}, filename={filename}")

    # Get the file path using the storage service
    file_path = storage_service.get_file_path(carousel_id, filename)

    # Log file path details
    logger.info(f"File path: {file_path}")
    logger.info(f"File exists: {file_path.exists() if file_path else False}")
    logger.info(f"temp_dir: {storage_service.temp_dir}")

    if not file_path or not file_path.exists() or not file_path.is_file():
        logger.error(f"File not found: {file_path}")
        if file_path and file_path.parent.exists():
            logger.info(
                f"Parent directory contents: {list(file_path.parent.iterdir())}"
            )
        raise HTTPException(status_code=404, detail="File not found")

    # Determine content type
    content_type = storage_service.get_content_type(filename)
    logger.info(f"Serving file with content type: {content_type}")

    return FileResponse(
        path=str(file_path),
        media_type=content_type,
        filename=filename
    )


@router.get("/debug-temp", tags=["debug"])
async def debug_temp():
    """Debug endpoint to check temp directory contents"""
    temp_dir = storage_service.temp_dir
    contents = {}

    # List all carousel directories
    try:
        for carousel_id in os.listdir(temp_dir):
            carousel_path = temp_dir / carousel_id
            if carousel_path.is_dir():
                contents[carousel_id] = os.listdir(carousel_path)

        return {
            "temp_dir": str(temp_dir),
            "contents": contents,
            "abs_path": str(temp_dir.absolute()),
            "exists": temp_dir.exists(),
            "is_dir": temp_dir.is_dir()
        }
    except Exception as e:
        return {
            "error": str(e),
            "temp_dir": str(temp_dir),
            "abs_path": str(temp_dir.absolute())
        }