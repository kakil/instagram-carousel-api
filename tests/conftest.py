"""
Pytest configuration file providing common fixtures for tests.
"""

import pytest
import os
import tempfile
from fastapi.testclient import TestClient
from pathlib import Path

# We need to import the StorageService class directly,
# not from app.main which can cause circular imports
from app.services.storage_service import StorageService
from app.services.image_service import get_image_service, ImageServiceType


# Import create_app directly to avoid circular dependencies
def get_app():
    from app.main import create_app
    return create_app()


@pytest.fixture
def app():
    """Create a test app instance."""
    return get_app()


@pytest.fixture
def client(app):
    """Create a test client for the app."""
    return TestClient(app)


@pytest.fixture
def temp_dir():
    """Create a temporary directory for tests."""
    with tempfile.TemporaryDirectory() as temp_dir:
        yield temp_dir


@pytest.fixture
def storage_service(temp_dir):
    """Create a storage service instance for tests."""
    service = StorageService()
    service.temp_dir = temp_dir
    return service


@pytest.fixture
def test_settings():
    """Test settings for services."""
    return {
        'width': 500,
        'height': 500,
        'bg_color': (18, 18, 18),
        'title_font': 'Arial.ttf',
        'text_font': 'Arial.ttf',
        'nav_font': 'Arial.ttf'
    }


@pytest.fixture
def test_image():
    """Create a test image data."""
    return {
        'carousel_id': 'test123',
        'carousel_title': 'Test Carousel',
        'slides': [
            {'text': 'This is slide 1'},
            {'text': 'This is slide 2'}
        ],
        'include_logo': False,
        'logo_path': None
    }