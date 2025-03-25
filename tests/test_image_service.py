"""
Tests for the image service module of Instagram Carousel Generator.

This module contains tests for the image generation functionality,
including slide creation, text sanitization, and error handling scenarios.
The tests cover both standard and enhanced implementations of the image service.
"""

from io import BytesIO

import pytest
from PIL import Image

# Import the image service components
from app.services.image_service import ImageServiceType, get_image_service


@pytest.fixture
def standard_image_service():
    """Fixture to provide a standard image service for tests."""
    settings = {
        "width": 500,  # Smaller size for faster tests
        "height": 500,
        "bg_color": (18, 18, 18),
        "title_font": "Arial.ttf",
        "text_font": "Arial.ttf",
        "nav_font": "Arial.ttf",
    }
    return get_image_service(ImageServiceType.STANDARD.value, settings)


@pytest.fixture
def enhanced_image_service():
    """Fixture to provide an enhanced image service for tests."""
    settings = {
        "width": 500,  # Smaller size for faster tests
        "height": 500,
        "bg_color": (18, 18, 18),
        "title_font": "Arial.ttf",
        "text_font": "Arial.ttf",
        "nav_font": "Arial.ttf",
    }
    return get_image_service(ImageServiceType.ENHANCED.value, settings)


def test_create_slide_image(enhanced_image_service):
    """Test the slide image creation functionality."""
    # Create a test image
    img = enhanced_image_service.create_slide_image(
        "Test Title", "This is test slide content", 1, 3, False, None
    )

    # Check if image was created
    assert img is not None
    assert isinstance(img, Image.Image)

    # Check image dimensions
    assert img.width == 500  # Should match our fixture settings
    assert img.height == 500

    # Save to BytesIO to verify it's a valid image
    buffer = BytesIO()
    img.save(buffer, format="PNG")
    buffer.seek(0)

    # Try to open saved image
    validate_img = Image.open(buffer)
    assert validate_img is not None


def test_create_carousel_images(enhanced_image_service):
    """Test the carousel images creation functionality."""
    # Set up test data
    carousel_title = "Test Carousel"
    slides_data = [{"text": "This is slide 1"}, {"text": "This is slide 2"}]
    carousel_id = "test123"

    # Create carousel images
    result = enhanced_image_service.create_carousel_images(carousel_title, slides_data, carousel_id)

    # Verify results
    assert len(result) == 2
    assert "filename" in result[0]
    assert "content" in result[0]
    assert result[0]["filename"] == "slide_1.png"
    assert result[1]["filename"] == "slide_2.png"


def test_error_slide(enhanced_image_service):
    """Test the error slide creation."""
    # Create an error slide
    error_slide = enhanced_image_service.create_error_slide(1, 3, "Test error message")

    # Verify it's a valid image
    assert error_slide is not None
    assert isinstance(error_slide, Image.Image)

    # Verify dimensions
    assert error_slide.width == 500
    assert error_slide.height == 500


def test_sanitize_text(enhanced_image_service):
    """Test text sanitization functionality."""
    # Test with various special characters
    special_text = "Test with special characters: → ← " " ' ' — – …"
    sanitized = enhanced_image_service.sanitize_text(special_text)

    # Verify basic sanitization
    assert "→" not in sanitized
    assert "->" in sanitized  # Check for replacement

    # Test with None input
    assert enhanced_image_service.sanitize_text(None) == ""

    # Test with non-string input
    assert isinstance(enhanced_image_service.sanitize_text(123), str)


def test_compare_service_implementations(standard_image_service, enhanced_image_service):
    """Test that both service implementations produce valid images."""
    # Test parameters
    title = "Test Title"
    text = "This is test content"
    slide_number = 1
    total_slides = 3

    # Create images with both services
    standard_img = standard_image_service.create_slide_image(
        title, text, slide_number, total_slides, False, None
    )

    enhanced_img = enhanced_image_service.create_slide_image(
        title, text, slide_number, total_slides, False, None
    )

    # Verify both are valid images
    assert isinstance(standard_img, Image.Image)
    assert isinstance(enhanced_img, Image.Image)

    # They should have the same dimensions as specified in the fixtures
    assert standard_img.width == enhanced_img.width == 500
    assert standard_img.height == enhanced_img.height == 500


def test_unicode_text_handling(enhanced_image_service):
    """Test handling of complex Unicode text."""
    # Text with various Unicode characters
    unicode_text = "Unicode test: 你好 Привет こんにちは 안녕하세요 αβγ ✓✗✘"

    # Create an image with Unicode text
    img = enhanced_image_service.create_slide_image("Unicode Test", unicode_text, 1, 1, False, None)

    # Verify image was created
    assert img is not None
    assert isinstance(img, Image.Image)

    # Save and verify it's a valid image
    buffer = BytesIO()
    img.save(buffer, format="PNG")
    buffer.seek(0)
    validate_img = Image.open(buffer)
    assert validate_img is not None


def test_error_handling_with_problematic_text(enhanced_image_service):
    """Test error handling with potentially problematic text."""
    # Create a very long text that might cause issues
    very_long_text = "This is an extremely long text " * 100

    # The service should handle this gracefully
    img = enhanced_image_service.create_slide_image(
        "Long Text Test", very_long_text, 1, 1, False, None
    )

    # Verify image was created despite the challenging input
    assert img is not None
    assert isinstance(img, Image.Image)
