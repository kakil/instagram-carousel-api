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
from typing import Dict, Any, List, Optional, Tuple
import traceback
from pathlib import Path

# Import model dependencies
from app.core.config import settings
from app.services.storage_service import StorageService
from app.services.image_service import BaseImageService
from app.api.security import validate_file_access, rate_limit
from app.core.models import (
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
# Add request logging middleware
async def log_request_info(http_request: Request):  # Renamed parameter here too
    """Log basic request information"""
    start_time = time.time()
    client_host = http_request.client.host if http_request.client else "unknown"
    logger.info(
        f"Request from {client_host} - {http_request.method} {http_request.url.path}"
    )
    return start_time


# Add background task for cleanup
def cleanup_temp_files(carousel_id: str):
    """Cleanup any temporary files created during carousel generation"""
    # This could be expanded to clean up any files stored temporarily
    logger.info(f"Cleaning up temporary files for carousel {carousel_id}")


# Use centralized dependencies
from app.api.dependencies import (
    get_enhanced_image_service, 
    get_standard_image_service,
    get_storage_service,
    get_heavy_rate_limit,
    log_request_info,
    cleanup_temp_files
)


# Apply more aggressive rate limiting to generation endpoints
heavy_rate_limit = rate_limit(max_requests=20, window_seconds=60)


@router.post("/generate-carousel", response_model=CarouselResponse, tags=["carousel"])
async def generate_carousel(
        request: CarouselRequest,
        background_tasks: BackgroundTasks,
        http_request: Request,
        image_service: BaseImageService = Depends(get_enhanced_image_service),
        _: None = Depends(get_heavy_rate_limit)
):
    start_time = await log_request_info(http_request) 
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
        http_request: Request,
        image_service: BaseImageService = Depends(get_enhanced_image_service),
        storage_service: StorageService = Depends(get_storage_service),
        _: None = Depends(heavy_rate_limit)
):
    try:
        # Log request
        start_time = await log_request_info(http_request)

        # Generate the carousel
        carousel_id, result = await _generate_carousel_content(
            request, image_service
        )

        # Process the results
        public_urls = await _save_and_prepare_urls(
            carousel_id, result, background_tasks, storage_service
        )

        # Prepare and return the response
        return _prepare_carousel_response(carousel_id, result, public_urls)

    except Exception as e:
        logger.error(f"Error generating carousel with URLs: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Error generating carousel: {str(e)}"
        )


async def _generate_carousel_content(
        request: CarouselRequest,
        image_service
) -> Tuple[str, List[Dict[str, Any]]]:
    """Generate carousel images based on request data"""
    # Create a unique ID for this carousel
    carousel_id = str(uuid.uuid4())[:8]
    logger.info(f"Starting carousel generation with URLs for ID: {carousel_id}")

    # Generate carousel images
    result = image_service.create_carousel_images(
        request.carousel_title,
        [{"text": slide.text} for slide in request.slides],
        carousel_id,
        request.include_logo,
        request.logo_path
    )

    return carousel_id, result


async def _save_and_prepare_urls(
        carousel_id: str,
        result: List[Dict[str, Any]],
        background_tasks: BackgroundTasks,
        storage_service: StorageService
) -> List[str]:
    """Save images and prepare public URLs for access"""
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

    return public_urls


def _prepare_carousel_response(
        carousel_id: str,
        result: List[Dict[str, Any]],
        public_urls: List[str]
) -> Dict[str, Any]:
    """Prepare the response data structure"""
    return {
        "status": "success",
        "carousel_id": carousel_id,
        "slides": result,
        "public_urls": public_urls
    }


@router.get("/temp/{carousel_id}/{filename}", tags=["files"])
async def get_temp_file(
    carousel_id: str, 
    filename: str,
    storage_service: StorageService = Depends(get_storage_service)
):
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
async def debug_temp(
    storage_service: StorageService = Depends(get_storage_service)
):
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