from fastapi import APIRouter, HTTPException
import uuid
import json
from app.models.carousel import CarouselRequest, CarouselResponse
from app.services.image_service import create_carousel_images
from fastapi.responses import JSONResponse
from typing import Any


router = APIRouter()

class CustomJSONResponse(JSONResponse):
    def render(self, content: Any) -> bytes:
        return json.dumps(
            content,
            ensure_ascii=False,
            allow_nan=False,
            indent=None,
            separators=(",", ":"),
        ).encode("utf-8")


@router.post("/generate-carousel",
             response_class=CustomJSONResponse,
             response_model=CarouselResponse,
             tags=["carousel"])

async def generate_carousel(request: CarouselRequest):
    """Generate carousel images from provided text content"""
    try:
        # Create a unique ID for this carousel
        carousel_id = str(uuid.uuid4())[:8]

        # Generate carousel images
        result = create_carousel_images(
            request.carousel_title,
            request.slides,
            carousel_id,
            request.include_logo,
            request.logo_path
        )

        return {
            "status": "success",
            "carousel_id": carousel_id,
            "slides": result
        }

    except Exception as e:
        raise HTTPException(status_code=500,
                            detail=f"Error generating carousel: {str(e)}")