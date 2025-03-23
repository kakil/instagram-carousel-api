"""
Data models for version 1 of the Instagram Carousel Generator API.

This module defines the v1 request and response models using Pydantic.
"""

from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any


class SlideContent(BaseModel):
    """Content for a single carousel slide"""
    text: str = Field(..., description="Text content for the slide")


class CarouselSettings(BaseModel):
    """Settings for carousel image generation"""
    width: Optional[int] = Field(None, description="Width of the carousel images in pixels")
    height: Optional[int] = Field(None, description="Height of the carousel images in pixels")
    bg_color: Optional[tuple] = Field(None, description="Background color as RGB tuple")
    title_font: Optional[str] = Field(None, description="Title font file name")
    text_font: Optional[str] = Field(None, description="Text font file name")
    nav_font: Optional[str] = Field(None, description="Navigation font file name")


class CarouselRequest(BaseModel):
    """Request model for carousel generation"""
    carousel_title: str = Field(..., description="Title for the carousel")
    slides: List[SlideContent] = Field(..., description="List of slide contents")
    include_logo: bool = Field(False, description="Whether to include a logo")
    logo_path: Optional[str] = Field(None, description="Path to logo file")
    settings: Optional[Dict[str, Any]] = Field(None, description="Custom settings for carousel generation")

    class Config:
        """Example configuration for API documentation"""
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
    carousel_id: str = Field(..., description="Unique identifier for the carousel")
    slides: List[SlideResponse] = Field(..., description="Generated slide images")
    processing_time: Optional[float] = Field(None, description="Processing time in seconds")
    warnings: List[str] = Field([], description="Any warnings during processing")


class CarouselResponseWithUrls(CarouselResponse):
    """Response model for carousel generation with public URLs"""
    public_urls: List[str] = Field([], description="Publicly accessible URLs for the slide images")


class ErrorResponse(BaseModel):
    """Response model for API errors"""
    detail: str = Field(..., description="Error message")
    status_code: int = Field(..., description="HTTP status code")
    error_type: Optional[str] = Field(None, description="Type of error")