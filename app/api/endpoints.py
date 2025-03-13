from fastapi import APIRouter, HTTPException, Request, BackgroundTasks
import uuid
import logging
import time
from typing import Dict, Any, List
from pydantic import BaseModel, Field
import traceback

# Import your improved image service
from app.services.improved_image_service import create_carousel_images, \
    ImageGenerationError

# Set up logging
logger = logging.getLogger(__name__)


# Define models
class SlideContent(BaseModel):
    """Content for a single carousel slide"""
    text: str = Field(..., description="Text content for the slide")


class CarouselRequest(BaseModel):
    """Request model for carousel generation"""
    carousel_title: str = Field(..., description="Title for the carousel")
    slides: List[SlideContent] = Field(...,
                                       description="List of slide contents")
    include_logo: bool = Field(False, description="Whether to include a logo")
    logo_path: str = Field(None, description="Path to logo file")
    settings: Dict[str, Any] = Field(None,
                                     description="Optional settings for image generation")

    class Config:
        schema_extra = {
            "example": {
                "carousel_title": "5 Productivity Tips",
                "slides": [
                    {"text": "Wake up early and plan your day"},
                    {"text": "Use the Pomodoro technique for focus"},
                    {"text": "Take regular breaks to recharge"}
                ],
                "include_logo": True,
                "logo_path": "static/assets/logo.png",
                "settings": {
                    "width": 1080,
                    "height": 1080,
                    "bg_color": [18, 18, 18]
                }
            }
        }


class SlideResponse(BaseModel):
    """Response model for a generated slide"""
    filename: str = Field(..., description="Filename of the generated image")
    content: str = Field(..., description="Hex-encoded image content")


class CarouselResponse(BaseModel):
    """Response model for carousel generation"""
    status: str = Field(..., description="Status of the operation")
    carousel_id: str = Field(...,
                             description="Unique identifier for the carousel")
    slides: List[SlideResponse] = Field(...,
                                        description="Generated slide images")
    processing_time: float = Field(None,
                                   description="Processing time in seconds")
    warnings: List[str] = Field([],
                                description="Any warnings during processing")


# Create a router for the carousel endpoints
router = APIRouter()


# Add request logging middleware
async def log_request_info(request: Request):
    """Log basic request information"""
    start_time = time.time()
    client_host = request.client.host if request.client else "unknown"
    logger.info(
        f"Request from {client_host} - {request.method} {request.url.path}")
    return start_time


# Add background task for cleanup
def cleanup_temp_files(carousel_id: str):
    """Cleanup any temporary files created during carousel generation"""
    # This could be expanded to clean up any files stored temporarily
    logger.info(f"Cleaning up temporary files for carousel {carousel_id}")


@router.post("/generate-carousel", response_model=CarouselResponse,
             tags=["carousel"])
async def generate_carousel(request: CarouselRequest,
                            background_tasks: BackgroundTasks, req: Request):
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
                    f"Slide {i + 1} contains non-ASCII characters which may not render correctly")
                logger.warning(
                    f"Non-ASCII characters detected in slide {i + 1}")

        # Default settings if none provided
        settings = request.settings or {
            'width': 1080,
            'height': 1080,
            'bg_color': (18, 18, 18),
            'title_font': 'Arial Bold.ttf',
            'text_font': 'Arial.ttf',
            'nav_font': 'Arial.ttf'
        }

        # Generate carousel images
        result = create_carousel_images(
            request.carousel_title,
            [{"text": slide.text} for slide in request.slides],
            carousel_id,
            settings,
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

    except ImageGenerationError as e:
        # Handle specific image generation errors
        logger.error(f"Image generation error: {str(e)}")
        raise HTTPException(status_code=422,
                            detail=f"Error generating carousel images: {str(e)}")
    except Exception as e:
        # Handle general errors
        logger.error(f"Unexpected error: {str(e)}")
        logger.error(traceback.format_exc())

        error_message = str(e)
        if "codec can't encode character" in error_message:
            error_message = f"Unicode character issue: {error_message}. Try removing special characters from your text."

        raise HTTPException(status_code=500,
                            detail=f"Error generating carousel: {error_message}")