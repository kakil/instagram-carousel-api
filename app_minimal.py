"""
Minimal implementation of the Instagram Carousel Generator API.

This module provides a simplified version of the Instagram Carousel Generator,
containing all core functionality in a single file for easier understanding and deployment.
It includes image generation utilities, API endpoints, and data models.
"""
import os
import tempfile
import uuid
from datetime import datetime
from typing import List, Optional

import uvicorn
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from PIL import Image, ImageDraw, ImageFont
from pydantic import BaseModel, Field

app = FastAPI(
    title="Instagram Carousel Generator API - Minimal",
    description="API for generating Instagram carousel images with consistent styling",
    version="1.0.0",
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Add health check endpoint
@app.get("/health")
async def health_check():
    """Check the health status of the API."""
    return {"status": "healthy", "timestamp": datetime.now().isoformat()}


# Define models directly in this file to avoid circular imports
class SlideContent(BaseModel):
    """Content for a single carousel slide."""

    text: str = Field(..., description="Text content for the slide")


class CarouselRequest(BaseModel):
    """Request model for carousel generation."""

    carousel_title: str = Field(..., description="Title for the carousel")
    slides: List[SlideContent] = Field(..., description="List of slide contents")
    include_logo: bool = Field(False, description="Whether to include a logo")
    logo_path: Optional[str] = Field(None, description="Path to logo file")


class SlideResponse(BaseModel):
    """Response model for a generated slide."""

    filename: str = Field(..., description="Filename of the generated image")
    content: str = Field(..., description="Hex-encoded image content")


class CarouselResponse(BaseModel):
    """Response model for carousel generation."""

    status: str = Field(..., description="Status of the operation")
    carousel_id: str = Field(..., description="Unique identifier for the carousel")
    slides: List[SlideResponse] = Field(..., description="Generated slide images")


# Define image utilities directly in this file
def create_gradient_text(draw, text, position, font, width, colors=None):
    """Create gradient text from one color to another."""
    if colors is None:
        # Default black to white gradient
        colors = [(0, 0, 0), (255, 255, 255)]

    # Get text size
    text_bbox = draw.textbbox((0, 0), text, font=font)
    text_width = text_bbox[2] - text_bbox[0]
    text_height = text_bbox[3] - text_bbox[1]

    # Create a gradient mask
    gradient = Image.new("L", (text_width, text_height), color=0)
    gradient_draw = ImageDraw.Draw(gradient)

    # Create gradient by drawing lines with increasing brightness
    for i in range(text_width):
        color_idx = i / text_width
        r = int(colors[0][0] + color_idx * (colors[1][0] - colors[0][0]))
        g = int(colors[0][1] + color_idx * (colors[1][1] - colors[0][1]))
        b = int(colors[0][2] + color_idx * (colors[1][2] - colors[0][2]))
        brightness = int((r + g + b) / 3)
        gradient_draw.line([(i, 0), (i, text_height)], fill=brightness)

    # Create a transparent image for the text
    text_img = Image.new("RGBA", (text_width, text_height), color=(0, 0, 0, 0))
    text_draw = ImageDraw.Draw(text_img)

    # Draw the text in white
    text_draw.text((0, 0), text, font=font, fill="white")

    # Apply the gradient mask to the text
    text_img.putalpha(gradient)

    # Calculate position to center the text
    x, y = position
    x = x - text_width // 2
    y = y - text_height // 2

    return text_img, (x, y)


def create_slide_image(title, text, slide_number, total_slides, include_logo=False, logo_path=None):
    """Create an Instagram carousel slide with the specified styling."""
    width, height = 1080, 1080  # Default image size
    bg_color = (18, 18, 18)  # Dark background
    image = Image.new("RGB", (width, height), bg_color)
    draw = ImageDraw.Draw(image)

    # Load fonts (using default for simplicity in this minimal version)
    title_font = ImageFont.load_default()
    text_font = ImageFont.load_default()
    navigation_font = ImageFont.load_default()

    # Add title with gradient effect (only on first slide)
    if title:
        # Create gradient text from black to white
        gradient_text, pos = create_gradient_text(
            draw,
            title,
            (width // 2, 150),
            title_font,
            width,
            [(0, 0, 0), (255, 255, 255)],  # Black to white gradient
        )
        image.paste(gradient_text, pos, gradient_text)

    # Add main text (simplified for minimal version)
    draw.text((width // 2, height // 2), text, fill="white", font=text_font, anchor="mm")

    # Add navigation arrows and slide counter
    if slide_number > 1:
        draw.text((40, height // 2), "←", fill="white", font=navigation_font)

    if slide_number < total_slides:
        draw.text((width - 40, height // 2), "→", fill="white", font=navigation_font)

    # Add slide counter
    counter_text = f"{slide_number}/{total_slides}"
    draw.text(
        (width // 2, height - 50),
        counter_text,
        fill="white",
        font=navigation_font,
        anchor="mm",
    )

    return image


def create_carousel_images(
    carousel_title, slides_data, carousel_id, include_logo=False, logo_path=None
):
    """Create carousel images for Instagram based on text content."""
    with tempfile.TemporaryDirectory() as temp_dir:
        image_files = []

        # Generate each slide
        for index, slide in enumerate(slides_data):
            slide_text = slide.text
            slide_number = index + 1
            total_slides = len(slides_data)

            # Create image
            img = create_slide_image(
                carousel_title if index == 0 else None,
                # Only show title on first slide
                slide_text,
                slide_number,
                total_slides,
                include_logo,
                logo_path,
            )

            # Save image
            filename = os.path.join(temp_dir, f"slide_{slide_number}.png")
            img.save(filename)

            # Read file and convert to hex
            with open(filename, "rb") as f:
                file_content = f.read()

            # Add to result
            image_files.append(
                {
                    "filename": f"slide_{slide_number}.png",
                    "content": file_content.hex(),  # Convert binary to hex for JSON
                }
            )

        return image_files


@app.post("/api/generate-carousel", response_model=CarouselResponse)
async def generate_carousel(request: CarouselRequest):
    """Generate carousel images from provided text content."""
    try:
        # Create a unique ID for this carousel
        carousel_id = str(uuid.uuid4())[:8]

        # Generate carousel images
        result = create_carousel_images(
            request.carousel_title,
            request.slides,
            carousel_id,
            request.include_logo,
            request.logo_path,
        )

        return {"status": "success", "carousel_id": carousel_id, "slides": result}

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error generating carousel: {str(e)}")


if __name__ == "__main__":
    uvicorn.run("app_minimal:app", host="localhost", port=5001, reload=True)
