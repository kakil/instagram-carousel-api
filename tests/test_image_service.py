import pytest
from PIL import Image
from app.services.image_service import create_slide_image
from app.models.carousel import SlideContent
from io import BytesIO


def test_create_slide_image():
    """Test the slide image creation functionality"""
    # Create a test image
    img = create_slide_image(
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
    assert img.width == 1080
    assert img.height == 1080

    # Save to BytesIO to verify it's a valid image
    buffer = BytesIO()
    img.save(buffer, format="PNG")
    buffer.seek(0)

    # Try to open saved image
    validate_img = Image.open(buffer)
    assert validate_img is not None