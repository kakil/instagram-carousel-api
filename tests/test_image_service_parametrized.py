"""
Parameterized tests for the image service.

This module demonstrates how to write parameterized tests
for the image service to test multiple inputs efficiently.
"""

import pytest
from PIL import Image
from io import BytesIO
import tempfile
from pathlib import Path
from typing import Dict, Any, List, Tuple

from app.services.image_service import get_image_service, ImageServiceType, BaseImageService


@pytest.fixture
def test_image_service(request) -> BaseImageService:
    """
    Parametrized fixture to create an image service based on service type.
    
    Args:
        request: Pytest request object containing the service_type parameter
        
    Returns:
        BaseImageService: An image service instance of the specified type
    """
    # Get service type from parameter or default to enhanced
    service_type = getattr(request, "param", ImageServiceType.ENHANCED.value)
    
    # Standard test settings
    settings = {
        'width': 500,  # Smaller size for faster tests
        'height': 500,
        'bg_color': (18, 18, 18),
        'title_font': 'Arial.ttf',
        'text_font': 'Arial.ttf',
        'nav_font': 'Arial.ttf'
    }
    
    return get_image_service(service_type, settings)


class TestImageServiceParametrized:
    """Parameterized tests for the image service."""
    
    @pytest.mark.parametrize("service_type", [
        ImageServiceType.STANDARD.value,
        ImageServiceType.ENHANCED.value
    ])
    def test_service_creation(self, service_type):
        """Test image service creation with different types."""
        # Common settings
        settings = {
            'width': 500,
            'height': 500,
            'bg_color': (18, 18, 18),
            'title_font': 'Arial.ttf',
            'text_font': 'Arial.ttf',
            'nav_font': 'Arial.ttf'
        }
        
        # Create service
        service = get_image_service(service_type, settings)
        
        # Verify
        assert service is not None
        assert isinstance(service, BaseImageService)
        assert service.width == settings['width']
        assert service.height == settings['height']
        
        # Verify type-specific implementations
        if service_type == ImageServiceType.ENHANCED.value:
            assert hasattr(service, "_log_operation")
    
    @pytest.mark.parametrize("test_image_service, expected_behavior", [
        # Standard service doesn't have advanced error handling
        (ImageServiceType.STANDARD.value, False),
        # Enhanced service has advanced error handling
        (ImageServiceType.ENHANCED.value, True)
    ], indirect=["test_image_service"])
    def test_error_handling_behavior(self, test_image_service, expected_behavior):
        """Test error handling behavior for different service types."""
        # Intentionally problematic input
        problematic_text = "x" * 10000  # Very long text
        
        if expected_behavior:
            # Enhanced service should handle this gracefully
            result = test_image_service.create_slide_image(
                "Error Test",
                problematic_text,
                1, 1, False, None
            )
            assert isinstance(result, Image.Image)
        else:
            # Standard service might not handle extreme cases well
            # Just verify it doesn't crash completely
            result = test_image_service.create_slide_image(
                "Error Test",
                problematic_text,
                1, 1, False, None
            )
            assert result is not None
    
    @pytest.mark.parametrize("title,text,num,total,expected_dimensions", [
        ("Test Title", "Test text", 1, 3, (500, 500)),
        ("", "", 1, 1, (500, 500)),
        ("Very long title " * 5, "Very long content " * 20, 1, 10, (500, 500)),
    ])
    def test_slide_dimensions(self, enhanced_image_service, title, text, num, total, expected_dimensions):
        """Test that slides always have the expected dimensions."""
        # Create slide
        img = enhanced_image_service.create_slide_image(
            title, text, num, total, False, None
        )
        
        # Verify dimensions
        assert img.width == expected_dimensions[0]
        assert img.height == expected_dimensions[1]
    
    @pytest.mark.parametrize("special_text,expected_replacements", [
        ("Text with arrow →", "->"),
        ("Text with quotes \"quoted\"", "\"quoted\""),
        ("Text with dash —", "-"),
        ("Text with apostrophe '", "'"),
        ("Text with ellipsis …", "..."),
    ])
    def test_text_sanitization(self, enhanced_image_service, special_text, expected_replacements):
        """Test text sanitization with various special characters."""
        sanitized = enhanced_image_service.sanitize_text(special_text)
        assert expected_replacements in sanitized
    
    @pytest.mark.parametrize("slides_data,expected_count", [
        ([{"text": "Slide 1"}], 1),
        ([{"text": "Slide 1"}, {"text": "Slide 2"}], 2),
        ([{"text": "Slide 1"}, {"text": "Slide 2"}, {"text": "Slide 3"}], 3),
    ])
    def test_carousel_image_count(self, enhanced_image_service, slides_data, expected_count):
        """Test that carousel generation creates the correct number of slides."""
        with tempfile.TemporaryDirectory() as temp_dir:
            # Generate carousel
            result = enhanced_image_service.create_carousel_images(
                "Test Carousel",
                slides_data,
                "test123"
            )
            
            # Verify count
            assert len(result) == expected_count
            
            # Verify all slides have filenames and content
            for i, slide in enumerate(result):
                assert "filename" in slide
                assert "content" in slide
                assert slide["filename"] == f"slide_{i+1}.png"