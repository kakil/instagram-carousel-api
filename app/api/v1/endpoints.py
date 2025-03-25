"""
API endpoints for version 1 of the Instagram Carousel Generator.

This module defines the v1 endpoints for carousel generation and management.
"""
import logging
import os
import time
import uuid
from typing import Any, Dict, List, Tuple

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, Request
from fastapi.responses import FileResponse

# Import all dependencies at the top of the file
from app.api.dependencies import (
    cleanup_temp_files,
    get_enhanced_image_service,
    get_heavy_rate_limit,
    get_storage_service,
)
from app.api.monitoring import track_carousel_generation
from app.api.security import rate_limit, validate_file_access

# Import model dependencies
from app.core.config import settings

# Import monitoring modules
from app.core.logging import get_request_logger, metrics_logger
from app.core.models import CarouselRequest, CarouselResponse, CarouselResponseWithUrls
from app.core.monitoring import monitor_performance_context
from app.services.image_service import BaseImageService
from app.services.storage_service import StorageService

# Set up logging
logger = logging.getLogger(__name__)

# Create a router for the v1 endpoints
router = APIRouter()

# Apply more aggressive rate limiting to generation endpoints
heavy_rate_limit = rate_limit(max_requests=20, window_seconds=60)


@router.post("/generate-carousel", response_model=CarouselResponse, tags=["carousel"])
async def generate_carousel(
    request: CarouselRequest,
    background_tasks: BackgroundTasks,
    http_request: Request,
    image_service: BaseImageService = Depends(get_enhanced_image_service),
    _: None = Depends(get_heavy_rate_limit),
):
    """
    Generate Instagram carousel images from text content.

    This endpoint creates a set of visually consistent images for Instagram carousels
    based on the provided text content. It handles unicode characters, applies consistent
    styling, and returns hex-encoded image data.

    Args:
        request: Carousel content including title, slides text, and logo preferences
        background_tasks: FastAPI background tasks for scheduling cleanup
        http_request: The FastAPI request object
        image_service: Service for generating carousel images
        _: Rate limiting dependency

    Returns:
        JSON response with status, carousel ID, slide images, and processing information

    Raises:
        HTTPException: 422 if slides list is empty or 500 if generation fails
    """
    # Get request-specific logger and start time
    start_time = time.time()
    request_id = getattr(http_request.state, "request_id", str(uuid.uuid4()))
    request_logger = get_request_logger(request_id)
    warnings = []

    # Log operation start with detailed info
    request_logger.info(
        "Starting carousel generation",
        extra={
            "extra": {
                "carousel_title": request.carousel_title,
                "slide_count": len(request.slides) if request.slides else 0,
                "include_logo": request.include_logo,
                "has_logo_path": bool(request.logo_path),
            }
        },
    )

    # Validate that slides list is not empty
    if not request.slides:
        request_logger.warning("Empty slides list in request")
        raise HTTPException(status_code=422, detail="Slides list cannot be empty")

    try:
        # Create a unique ID for this carousel
        carousel_id = str(uuid.uuid4())[:8]
        request_logger.info(f"Assigned carousel ID: {carousel_id}")

        # Check for potentially problematic characters in text
        for i, slide in enumerate(request.slides):
            if any(ord(c) > 127 for c in slide.text):
                warnings.append(
                    f"Slide {i + 1} contains non-ASCII characters which may not render correctly"
                )
                request_logger.warning(
                    f"Non-ASCII characters detected in slide {i + 1}",
                    extra={"extra": {"slide_index": i, "carousel_id": carousel_id}},
                )

        # Use performance monitoring around the image generation
        with monitor_performance_context(
            "carousel_image_generation", carousel_id=carousel_id, num_slides=len(request.slides)
        ):
            # Generate carousel images using the image service
            result = image_service.create_carousel_images(
                request.carousel_title,
                [{"text": slide.text} for slide in request.slides],
                carousel_id,
                request.include_logo,
                request.logo_path,
            )

        # Schedule cleanup
        background_tasks.add_task(cleanup_temp_files, carousel_id)

        # Calculate processing time
        processing_time = time.time() - start_time
        processing_time_ms = processing_time * 1000
        processing_time_rounded = round(processing_time, 2)

        # Log successful generation with metrics
        request_logger.info(
            f"Carousel {carousel_id} generated successfully in {processing_time_rounded}s",
            extra={
                "extra": {
                    "carousel_id": carousel_id,
                    "duration_ms": processing_time_ms,
                    "num_slides": len(request.slides),
                    "slide_count": len(result),
                    "has_warnings": bool(warnings),
                }
            },
        )

        # Record metrics for carousel generation
        metrics_logger.log_carousel_generation(
            carousel_id=carousel_id,
            num_slides=len(result),
            duration_ms=processing_time_ms,
            success=True,
        )

        # Track carousel generation metrics
        track_carousel_generation(
            carousel_id=carousel_id,
            num_slides=len(result),
            duration_ms=processing_time_ms,
            success=True,
        )

        return {
            "status": "success",
            "carousel_id": carousel_id,
            "slides": result,
            "processing_time": processing_time_rounded,
            "warnings": warnings,
        }

    except Exception as e:
        # Calculate processing time even for failures
        processing_time_ms = (time.time() - start_time) * 1000

        # Log detailed error information
        request_logger.error(
            f"Error generating carousel: {str(e)}",
            exc_info=True,
            extra={
                "extra": {
                    "carousel_title": request.carousel_title,
                    "error_type": type(e).__name__,
                    "duration_ms": processing_time_ms,
                    "slide_count": len(request.slides) if request.slides else 0,
                }
            },
        )

        # Record error metrics
        metrics_logger.log_carousel_generation(
            carousel_id=carousel_id if "carousel_id" in locals() else "unknown",
            num_slides=len(request.slides) if request.slides else 0,
            duration_ms=processing_time_ms,
            success=False,
            error=str(e),
        )

        # Track carousel generation error metrics
        if "carousel_id" in locals():
            track_carousel_generation(
                carousel_id=carousel_id,
                num_slides=len(request.slides) if request.slides else 0,
                duration_ms=processing_time_ms,
                success=False,
            )

        # Prepare user-friendly error message
        error_message = str(e)
        if "codec can't encode character" in error_message:
            error_message = f"Unicode character issue: {error_message}. Try removing special characters from your text."

        raise HTTPException(status_code=500, detail=f"Error generating carousel: {error_message}")


@router.post(
    "/generate-carousel-with-urls",
    response_model=CarouselResponseWithUrls,
    tags=["carousel"],
)
async def generate_carousel_with_urls(
    request: CarouselRequest,
    background_tasks: BackgroundTasks,
    http_request: Request,
    image_service: BaseImageService = Depends(get_enhanced_image_service),
    storage_service: StorageService = Depends(get_storage_service),
    _: None = Depends(heavy_rate_limit),
):
    """
    Generate Instagram carousel images and return public URLs for accessing them.

    This endpoint creates a set of visually consistent images for Instagram carousels
    from the provided text content, stores them temporarily, and returns public URLs
    for accessing the generated images.

    Args:
        request: Carousel content including title, slides text, and logo preferences
        background_tasks: FastAPI background tasks for scheduling cleanup
        http_request: The FastAPI request object
        image_service: Service for generating carousel images
        storage_service: Service for storing and managing temporary files
        _: Rate limiting dependency

    Returns:
        JSON response with status, carousel ID, slide images data, and public URLs

    Raises:
        HTTPException: 422 if slides list is empty or 500 if generation fails
    """
    # Get request-specific logger and start time
    start_time = time.time()
    request_id = getattr(http_request.state, "request_id", str(uuid.uuid4()))
    request_logger = get_request_logger(request_id)

    # Log operation start
    request_logger.info(
        "Starting carousel generation with URLs",
        extra={
            "extra": {
                "carousel_title": request.carousel_title,
                "slide_count": len(request.slides) if request.slides else 0,
            }
        },
    )

    # Validate that slides list is not empty
    if not request.slides:
        request_logger.warning("Empty slides list in request")
        raise HTTPException(status_code=422, detail="Slides list cannot be empty")

    try:
        # Generate the carousel with performance monitoring
        with monitor_performance_context("carousel_generation_with_urls"):
            carousel_id, result = await _generate_carousel_content(request, image_service)

        # Process the results
        public_urls = await _save_and_prepare_urls(
            carousel_id, result, background_tasks, storage_service
        )

        # Calculate processing time
        processing_time_ms = (time.time() - start_time) * 1000

        # Log successful completion
        request_logger.info(
            "Carousel with URLs generated successfully",
            extra={
                "extra": {
                    "carousel_id": carousel_id,
                    "duration_ms": processing_time_ms,
                    "num_slides": len(result),
                    "url_count": len(public_urls),
                }
            },
        )

        # Record metrics
        metrics_logger.log_carousel_generation(
            carousel_id=carousel_id,
            num_slides=len(result),
            duration_ms=processing_time_ms,
            success=True,
        )

        # Track metrics
        track_carousel_generation(
            carousel_id=carousel_id,
            num_slides=len(result),
            duration_ms=processing_time_ms,
            success=True,
        )

        # Prepare and return the response
        return _prepare_carousel_response(carousel_id, result, public_urls)

    except Exception as e:
        # Calculate processing time for failure
        processing_time_ms = (time.time() - start_time) * 1000

        # Log error
        request_logger.error(
            f"Error generating carousel with URLs: {str(e)}",
            exc_info=True,
            extra={
                "extra": {
                    "error_type": type(e).__name__,
                    "duration_ms": processing_time_ms,
                }
            },
        )

        # Record error metrics if carousel_id was created
        if "carousel_id" in locals():
            metrics_logger.log_carousel_generation(
                carousel_id=carousel_id,
                num_slides=len(request.slides) if request.slides else 0,
                duration_ms=processing_time_ms,
                success=False,
                error=str(e),
            )

            track_carousel_generation(
                carousel_id=carousel_id,
                num_slides=len(request.slides) if request.slides else 0,
                duration_ms=processing_time_ms,
                success=False,
            )

        logger.error(f"Error generating carousel with URLs: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error generating carousel: {str(e)}")


async def _generate_carousel_content(
    request: CarouselRequest, image_service
) -> Tuple[str, List[Dict[str, Any]]]:
    """Generate carousel images based on request data."""
    # Create a unique ID for this carousel
    carousel_id = str(uuid.uuid4())[:8]
    logger.info(f"Starting carousel generation with URLs for ID: {carousel_id}")

    # Generate carousel images
    result = image_service.create_carousel_images(
        request.carousel_title,
        [{"text": slide.text} for slide in request.slides],
        carousel_id,
        request.include_logo,
        request.logo_path,
    )

    return carousel_id, result


async def _save_and_prepare_urls(
    carousel_id: str,
    result: List[Dict[str, Any]],
    background_tasks: BackgroundTasks,
    storage_service: StorageService,
) -> List[str]:
    """Save images and prepare public URLs for access."""
    # Record start time for performance monitoring
    start_time = time.time()

    # Determine base URL for public access - use configuration
    base_url = settings.PUBLIC_BASE_URL

    # Save images and get public URLs
    public_urls = storage_service.save_carousel_images(carousel_id, result, base_url)

    # Schedule cleanup of these files after configured lifetime
    carousel_dir = storage_service.temp_dir / carousel_id
    storage_service.schedule_cleanup(
        background_tasks, carousel_dir, hours=settings.TEMP_FILE_LIFETIME_HOURS
    )

    # Log performance metrics
    duration_ms = (time.time() - start_time) * 1000
    metrics_logger.log_image_processing(
        operation="save_carousel_images",
        image_size=(settings.DEFAULT_WIDTH, settings.DEFAULT_HEIGHT),
        duration_ms=duration_ms,
        success=True,
    )

    return public_urls


def _prepare_carousel_response(
    carousel_id: str, result: List[Dict[str, Any]], public_urls: List[str]
) -> Dict[str, Any]:
    """Prepare the response data structure."""
    return {
        "status": "success",
        "carousel_id": carousel_id,
        "slides": result,
        "public_urls": public_urls,
    }


@router.get("/temp/{carousel_id}/{filename}", tags=["files"])
async def get_temp_file(
    carousel_id: str,
    filename: str,
    request: Request,
    storage_service: StorageService = Depends(get_storage_service),
):
    """Serve a temporary file with proper content type."""
    # Get request logger
    request_id = getattr(request.state, "request_id", str(uuid.uuid4()))
    request_logger = get_request_logger(request_id)

    # Record start time
    start_time = time.time()

    try:
        # Validate file access parameters to prevent directory traversal
        validate_file_access(carousel_id, filename)

        # Log request info
        request_logger.info(
            f"File request: carousel_id={carousel_id}, filename={filename}",
            extra={"extra": {"carousel_id": carousel_id, "filename": filename}},
        )

        # Get the file path using the storage service
        file_path = storage_service.get_file_path(carousel_id, filename)

        # Log file path details at debug level
        request_logger.debug(
            "File path details",
            extra={
                "extra": {
                    "file_path": str(file_path),
                    "exists": file_path.exists() if file_path else False,
                    "temp_dir": str(storage_service.temp_dir),
                }
            },
        )

        if not file_path or not file_path.exists() or not file_path.is_file():
            request_logger.error(
                f"File not found: {file_path}",
                extra={"extra": {"carousel_id": carousel_id, "filename": filename}},
            )

            # List directory contents for debugging
            if file_path and file_path.parent.exists():
                parent_contents = list(file_path.parent.iterdir())
                request_logger.debug(
                    "Parent directory contents",
                    extra={"extra": {"parent_contents": [str(p) for p in parent_contents]}},
                )

            raise HTTPException(status_code=404, detail="File not found")

        # Determine content type
        content_type = storage_service.get_content_type(filename)

        # Log file access success with metrics
        duration_ms = (time.time() - start_time) * 1000
        metrics_logger.log_request(
            request_id=request_id,
            method="GET",
            path=f"/temp/{carousel_id}/{filename}",
            status_code=200,
            duration_ms=duration_ms,
            ip_address=request.client.host if request.client else "unknown",
            user_agent=request.headers.get("user-agent"),
            extra={"file_type": content_type, "carousel_id": carousel_id},
        )

        return FileResponse(path=str(file_path), media_type=content_type, filename=filename)

    except HTTPException as e:
        # Log metrics for HTTP exceptions
        duration_ms = (time.time() - start_time) * 1000
        metrics_logger.log_request(
            request_id=request_id,
            method="GET",
            path=f"/temp/{carousel_id}/{filename}",
            status_code=e.status_code,
            duration_ms=duration_ms,
            ip_address=request.client.host if request.client else "unknown",
            user_agent=request.headers.get("user-agent"),
            extra={"error": e.detail, "carousel_id": carousel_id},
        )
        raise

    except Exception as e:
        # Log unexpected errors
        request_logger.error(
            f"Unexpected error serving file: {str(e)}",
            exc_info=True,
            extra={"extra": {"carousel_id": carousel_id, "filename": filename}},
        )

        # Log metrics for unexpected errors
        duration_ms = (time.time() - start_time) * 1000
        metrics_logger.log_request(
            request_id=request_id,
            method="GET",
            path=f"/temp/{carousel_id}/{filename}",
            status_code=500,
            duration_ms=duration_ms,
            ip_address=request.client.host if request.client else "unknown",
            user_agent=request.headers.get("user-agent"),
            extra={"error": str(e), "carousel_id": carousel_id},
        )

        raise HTTPException(status_code=500, detail=f"Error serving file: {str(e)}")


@router.get("/debug-temp", tags=["debug"])
async def debug_temp(
    request: Request, storage_service: StorageService = Depends(get_storage_service)
):
    """Debug endpoint to check temp directory contents."""
    # Get request logger
    request_id = getattr(request.state, "request_id", str(uuid.uuid4()))
    request_logger = get_request_logger(request_id)

    # Record start time
    start_time = time.time()

    request_logger.info("Debug temp directory request")

    temp_dir = storage_service.temp_dir
    contents = {}

    # List all carousel directories
    try:
        for carousel_id in os.listdir(temp_dir):
            carousel_path = temp_dir / carousel_id
            if carousel_path.is_dir():
                contents[carousel_id] = os.listdir(carousel_path)

        result = {
            "temp_dir": str(temp_dir),
            "contents": contents,
            "abs_path": str(temp_dir.absolute()),
            "exists": temp_dir.exists(),
            "is_dir": temp_dir.is_dir(),
        }

        # Log metrics
        duration_ms = (time.time() - start_time) * 1000
        metrics_logger.log_request(
            request_id=request_id,
            method="GET",
            path="/debug-temp",
            status_code=200,
            duration_ms=duration_ms,
            ip_address=request.client.host if request.client else "unknown",
            user_agent=request.headers.get("user-agent"),
            extra={"carousel_count": len(contents)},
        )

        return result

    except Exception as e:
        # Log error
        request_logger.error(f"Error in debug-temp endpoint: {str(e)}", exc_info=True)

        # Log metrics
        duration_ms = (time.time() - start_time) * 1000
        metrics_logger.log_request(
            request_id=request_id,
            method="GET",
            path="/debug-temp",
            status_code=500,
            duration_ms=duration_ms,
            ip_address=request.client.host if request.client else "unknown",
            user_agent=request.headers.get("user-agent"),
            extra={"error": str(e)},
        )

        return {
            "error": str(e),
            "temp_dir": str(temp_dir),
            "abs_path": str(temp_dir.absolute()),
        }
