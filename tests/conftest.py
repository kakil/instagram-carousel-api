"""
Pytest configuration file providing common fixtures for tests.

This module defines fixtures that can be used across all test files,
promoting test modularity and reducing code duplication.
"""

import pytest
import os
import tempfile
import time
import json
import logging
from unittest.mock import MagicMock, patch
from fastapi.testclient import TestClient
from fastapi import Request, FastAPI
from pathlib import Path
from typing import Dict, Any, List, Generator, Optional

# We need to import the StorageService class directly,
# not from app.main which can cause circular imports
from app.services.storage_service import StorageService
from app.services.image_service import get_image_service, ImageServiceType, BaseImageService
from app.api.dependencies import (
    get_enhanced_image_service, 
    get_storage_service, 
    get_api_key,
    log_request_info,
    set_v1_api_version
)
from app.core.models import CarouselRequest


# Import create_app directly to avoid circular dependencies
def get_app():
    from app.main import create_app
    return create_app()


# Application fixtures
@pytest.fixture
def app() -> FastAPI:
    """
    Create a test app instance.
    
    Returns:
        FastAPI: The FastAPI application instance
    """
    return get_app()


@pytest.fixture
def client(app: FastAPI) -> TestClient:
    """
    Create a test client for the app.
    
    Args:
        app: The FastAPI application
        
    Returns:
        TestClient: A FastAPI test client
    """
    return TestClient(app)


# Directory and file fixtures
@pytest.fixture
def temp_dir() -> Generator[str, None, None]:
    """
    Create a temporary directory for tests.
    
    Yields:
        str: Path to the temporary directory
    """
    with tempfile.TemporaryDirectory() as temp_dir:
        yield temp_dir


@pytest.fixture
def temp_file() -> Generator[str, None, None]:
    """
    Create a temporary file for tests.
    
    Yields:
        str: Path to the temporary file
    """
    with tempfile.NamedTemporaryFile(delete=False) as temp_file:
        yield temp_file.name
    # Clean up after test
    if os.path.exists(temp_file.name):
        os.unlink(temp_file.name)


# Service fixtures
@pytest.fixture
def storage_service(temp_dir: str) -> StorageService:
    """
    Create a storage service instance for tests.
    
    Args:
        temp_dir: Path to a temporary directory
        
    Returns:
        StorageService: A configured storage service
    """
    service = StorageService()
    service.temp_dir = Path(temp_dir)
    return service


@pytest.fixture
def standard_image_service() -> BaseImageService:
    """
    Fixture to provide a standard image service for tests.
    
    Returns:
        BaseImageService: A standard image service instance
    """
    settings = {
        'width': 500,  # Smaller size for faster tests
        'height': 500,
        'bg_color': (18, 18, 18),
        'title_font': 'Arial.ttf',
        'text_font': 'Arial.ttf',
        'nav_font': 'Arial.ttf'
    }
    return get_image_service(ImageServiceType.STANDARD.value, settings)


@pytest.fixture
def enhanced_image_service() -> BaseImageService:
    """
    Fixture to provide an enhanced image service for tests.
    
    Returns:
        BaseImageService: An enhanced image service instance
    """
    settings = {
        'width': 500,  # Smaller size for faster tests
        'height': 500,
        'bg_color': (18, 18, 18),
        'title_font': 'Arial.ttf',
        'text_font': 'Arial.ttf',
        'nav_font': 'Arial.ttf'
    }
    return get_image_service(ImageServiceType.ENHANCED.value, settings)


# Mock fixtures
@pytest.fixture
def mock_image_service() -> MagicMock:
    """
    Create a mock image service for testing.
    
    Returns:
        MagicMock: A mock image service
    """
    mock_service = MagicMock(spec=BaseImageService)

    # Set up mock return values
    mock_service.create_carousel_images.return_value = [
        {
            "filename": "slide_1.png",
            "content": "fake_hex_content"
        }
    ]
    
    # Add additional common mock methods
    mock_service.create_slide_image.return_value = MagicMock()  # Returns a mock PIL Image
    mock_service.create_error_slide.return_value = MagicMock()  # Returns a mock PIL Image
    mock_service.sanitize_text.side_effect = lambda x: str(x) if x is not None else ""

    return mock_service


@pytest.fixture
def mock_storage_service(temp_dir: str) -> MagicMock:
    """
    Create a mock storage service for testing.
    
    Args:
        temp_dir: Path to a temporary directory
        
    Returns:
        MagicMock: A mock storage service
    """
    mock_service = MagicMock(spec=StorageService)

    # Set up mock return values
    mock_service.save_carousel_images.return_value = ["http://test-url.com/temp/test123/slide_1.png"]

    # Mock temp directory methods
    temp_path = Path(temp_dir)
    os.makedirs(temp_path, exist_ok=True)
    mock_service.temp_dir = temp_path

    # Mock the get_file_path method to return a Path object that can be patched
    mock_path = MagicMock(spec=Path)
    mock_service.get_file_path.return_value = mock_path
    mock_path.exists.return_value = True
    mock_path.is_file.return_value = True
    mock_path.__str__.return_value = str(temp_path / "test123" / "slide_1.png")
    
    # Additional commonly used methods
    mock_service.get_content_type.return_value = "image/png"
    mock_service.schedule_cleanup.return_value = None
    
    return mock_service


@pytest.fixture
def test_request() -> MagicMock:
    """
    Create a mock request object for testing.
    
    Returns:
        MagicMock: A mock FastAPI Request object
    """
    mock_req = MagicMock(spec=Request)
    mock_req.client = MagicMock()
    mock_req.client.host = "127.0.0.1"
    mock_req.method = "POST"
    mock_req.url = MagicMock()
    mock_req.url.path = "/api/v1/test"
    mock_req.state = MagicMock()
    
    return mock_req


@pytest.fixture
def client_with_mocks(
    app: FastAPI, 
    mock_image_service: MagicMock, 
    mock_storage_service: MagicMock, 
    test_request: MagicMock
) -> TestClient:
    """
    Create a test client with mocked dependencies.
    
    This fixture sets up a FastAPI test client with all key
    dependencies mocked for isolated testing of endpoints.
    
    Args:
        app: The FastAPI application
        mock_image_service: A mock image service
        mock_storage_service: A mock storage service
        test_request: A mock request object
        
    Returns:
        TestClient: A FastAPI test client with dependency overrides
    """
    # Set up dependency overrides
    app.dependency_overrides = {
        get_enhanced_image_service: lambda: mock_image_service,
        get_storage_service: lambda: mock_storage_service,
        get_api_key: lambda: True,
        log_request_info: lambda: time.time(),  # Mock the request logging dependency
        Request: lambda: test_request,  # Mock the Request dependency to fix routing issues
        set_v1_api_version: lambda: None,  # Mock API versioning function
    }

    # Create a test client
    client = TestClient(app)

    yield client

    # Clean up
    app.dependency_overrides = {}


# Test data fixtures
@pytest.fixture
def test_settings() -> Dict[str, Any]:
    """
    Test settings for services.
    
    Returns:
        Dict[str, Any]: A dictionary of test settings
    """
    return {
        'width': 500,
        'height': 500,
        'bg_color': (18, 18, 18),
        'title_font': 'Arial.ttf',
        'text_font': 'Arial.ttf',
        'nav_font': 'Arial.ttf'
    }


@pytest.fixture
def test_image() -> Dict[str, Any]:
    """
    Create test image data.
    
    Returns:
        Dict[str, Any]: Test image data dictionary
    """
    return {
        'carousel_id': 'test123',
        'carousel_title': 'Test Carousel',
        'slides': [
            {'text': 'This is slide 1'},
            {'text': 'This is slide 2'}
        ],
        'include_logo': False,
        'logo_path': None,
        'settings': None
    }


@pytest.fixture
def carousel_request_data() -> Dict[str, Any]:
    """
    Create test carousel request data that matches the CarouselRequest model.
    
    Returns:
        Dict[str, Any]: A dictionary of carousel request data
    """
    return {
        'carousel_title': 'Test Carousel',
        'slides': [
            {'text': 'This is slide 1'},
            {'text': 'This is slide 2'}
        ],
        'include_logo': False,
        'logo_path': None,
        'settings': None
    }


@pytest.fixture
def carousel_request(carousel_request_data: Dict[str, Any]) -> CarouselRequest:
    """
    Create a CarouselRequest model instance for testing.
    
    Args:
        carousel_request_data: Dictionary of carousel request data
        
    Returns:
        CarouselRequest: A CarouselRequest model instance
    """
    return CarouselRequest(**carousel_request_data)


# Configure logging for tests
@pytest.fixture(autouse=True)
def configure_test_logging():
    """
    Configure logging for tests.
    
    This fixture is automatically used in all tests to configure
    logging appropriately for the test environment.
    """
    # Set up logging to console with a reasonable level
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    )
    
    # Optionally reduce noise from third-party libraries
    logging.getLogger('httpx').setLevel(logging.WARNING)
    logging.getLogger('urllib3').setLevel(logging.WARNING)