import pytest
from PIL import Image
from io import BytesIO
import os
import tempfile

# Import the new image service
from app.services.image_service import get_image_service, ImageServiceType


@pytest.fixture
def image_service():
    """Fixture to provide an image service for tests"""
    settings = {
        'width': 500,  # Smaller size for faster tests
        'height': 500,
        'bg_color': (18, 18, 18),
        'title_font': 'Arial.ttf',
        'text_font': 'Arial.ttf',
        'nav_font': 'Arial.ttf'
    }
    return get_image_service(ImageServiceType.ENHANCED.value, settings)


def test_create_slide_image(image_service):
    """Test the slide image creation functionality"""
    # Create a test image
    img = image_service.create_slide_image(
        "Test Title",
        "This is test slide content",
        1,
        3,
        False,
        None
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


def test_create_carousel_images(image_service):
    """Test the carousel images creation functionality"""
    with tempfile.TemporaryDirectory() as temp_dir:
        # Set up test data
        carousel_title = "Test Carousel"
        slides_data = [
            {"text": "This is slide 1"},
            {"text": "This is slide 2"}
        ]
        carousel_id = "test123"

        # Create carousel images
        result = image_service.create_carousel_images(
            carousel_title,
            slides_data,
            carousel_id
        )

        # Verify results
        assert len(result) == 2
        assert "filename" in result[0]
        assert "content" in result[0]
        assert result[0]["filename"] == "slide_1.png"
        assert result[1]["filename"] == "slide_2.png"


def test_error_slide(image_service):
    """Test the error slide creation"""
    # Create an error slide
    error_slide = image_service.create_error_slide(1, 3, "Test error message")

    # Verify it's a valid image
    assert error_slide is not None
    assert isinstance(error_slide, Image.Image)

    # Verify dimensions
    assert error_slide.width == 500
    assert error_slide.height == 500


def test_sanitize_text(image_service):
    """Test text sanitization functionality"""
    # Test with various special characters
    special_text = "Test with special characters: → ← " " ' ' — – …"
    sanitized = image_service.sanitize_text(special_text)

    # Verify basic sanitization
    assert "→" not in sanitized
    assert "->" in sanitized  # Check for replacement

    # Test with None input
    assert image_service.sanitize_text(None) == ""

    # Test with non-string input
    assert isinstance(image_service.sanitize_text(123), str)