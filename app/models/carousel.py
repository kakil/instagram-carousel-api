from pydantic import BaseModel, Field
from typing import List, Optional


class SlideContent(BaseModel):
    """Content for a single carousel slide"""
    text: str = Field(..., description="Text content for the slide")


class CarouselRequest(BaseModel):
    """Request model for carousel generation"""
    carousel_title: str = Field(..., description="Title for the carousel")
    slides: List[SlideContent] = Field(...,
                                       description="List of slide contents")
    include_logo: bool = Field(False, description="Whether to include a logo")
    logo_path: Optional[str] = Field(None, description="Path to logo file")

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
                "logo_path": "static/assets/logo.png"
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