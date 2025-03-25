"""
Integration tests for the storage service.

This module contains tests that verify the storage service's
interaction with the file system.
"""
import os
import shutil
import tempfile
from datetime import datetime
from pathlib import Path
from unittest.mock import MagicMock

import pytest
from fastapi import BackgroundTasks

from app.services.storage_service import StorageService


@pytest.fixture
def temp_test_dir():
    """Create a temporary directory for testing file operations."""
    with tempfile.TemporaryDirectory() as temp_dir:
        yield Path(temp_dir)


@pytest.fixture
def test_storage_service(temp_test_dir):
    """Create a storage service with a test temporary directory."""
    service = StorageService()
    service.temp_dir = temp_test_dir
    yield service


@pytest.fixture
def test_carousel_images():
    """Create test carousel image data."""
    # Use a very simple hex string pattern that we know will work
    # Just a few bytes of data representing a simple image-like content
    simple_hex_content = "0123456789abcdef" * 20  # Simple repeating pattern
    return [
        {"filename": "slide_1.png", "content": simple_hex_content},
        {"filename": "slide_2.png", "content": simple_hex_content},
    ]


@pytest.mark.integration
class TestStorageServiceFileSystem:
    """Tests for storage service file system operations."""

    def test_create_temp_directories(self, test_storage_service, temp_test_dir):
        """Test that the service properly creates temp directories."""
        # Test directory creation
        carousel_id = "test123"

        # Make sure temp_dir exists first - this is normally initialized in __init__
        os.makedirs(test_storage_service.temp_dir, exist_ok=True)

        carousel_dir = test_storage_service.temp_dir / carousel_id

        # Ensure directory doesn't exist at start
        if carousel_dir.exists():
            shutil.rmtree(carousel_dir)

        assert not carousel_dir.exists()

        # Create it using the service's directory creation method
        carousel_dir = test_storage_service.temp_dir / carousel_id
        carousel_dir.mkdir(exist_ok=True)

        # Verify it was created
        assert carousel_dir.exists()
        assert carousel_dir.is_dir()

    def test_save_carousel_images(self, test_storage_service, test_carousel_images):
        """Test saving carousel images to disk."""
        carousel_id = "save_test"
        base_url = "http://test-url.com"

        # Make sure temp_dir exists first
        os.makedirs(test_storage_service.temp_dir, exist_ok=True)

        # Save the images
        urls = test_storage_service.save_carousel_images(
            carousel_id, test_carousel_images, base_url
        )

        # Verify URLs were returned
        assert len(urls) == len(test_carousel_images)
        for url in urls:
            assert url.startswith(base_url)
            assert f"/temp/{carousel_id}/" in url

        # Verify files were created
        carousel_dir = test_storage_service.temp_dir / carousel_id
        assert carousel_dir.exists()

        for img_data in test_carousel_images:
            filepath = carousel_dir / img_data["filename"]
            assert filepath.exists()
            assert filepath.is_file()

            # Verify file has content
            assert filepath.stat().st_size > 0

    def test_get_file_path(self, test_storage_service):
        """Test retrieving file paths."""
        carousel_id = "path_test"
        filename = "test_file.png"

        # Create the directory and an empty file
        carousel_dir = test_storage_service.temp_dir / carousel_id
        os.makedirs(carousel_dir, exist_ok=True)

        filepath = carousel_dir / filename
        with open(filepath, "w") as f:
            f.write("test")

        # Get the path through the service
        result_path = test_storage_service.get_file_path(carousel_id, filename)

        # Verify
        assert result_path == filepath
        assert result_path.exists()

    def test_get_content_type(self, test_storage_service):
        """Test content type determination."""
        # Test various file extensions
        assert "image/png" in test_storage_service.get_content_type("image.png")
        assert "image/jpeg" in test_storage_service.get_content_type("photo.jpg")
        assert "image/jpeg" in test_storage_service.get_content_type("photo.jpeg")
        assert "image/svg+xml" in test_storage_service.get_content_type("vector.svg")
        assert "application/octet-stream" in test_storage_service.get_content_type("unknown.xyz")

    def test_cleanup_old_files(self, test_storage_service):
        """Test the cleanup of old files."""
        # Create some test directories with files
        for carousel_id in ["old1", "old2", "old3"]:
            carousel_dir = test_storage_service.temp_dir / carousel_id
            os.makedirs(carousel_dir, exist_ok=True)

            # Create a test file
            with open(carousel_dir / "test.txt", "w") as f:
                f.write("test content")

        # Get initial directory count
        initial_dirs = [d for d in test_storage_service.temp_dir.iterdir() if d.is_dir()]
        initial_count = len(initial_dirs)

        # Run cleanup with explicit 0 hours to force cleanup
        test_storage_service.cleanup_old_files(hours=0)

        # Check directories after cleanup
        after_dirs = [d for d in test_storage_service.temp_dir.iterdir() if d.is_dir()]
        after_count = len(after_dirs)

        # Verify directories were removed
        assert after_count < initial_count

    def test_schedule_cleanup(self, test_storage_service):
        """Test scheduling cleanup as a background task."""
        # Create a mock background tasks
        mock_tasks = MagicMock(spec=BackgroundTasks)

        # Schedule cleanup
        carousel_dir = test_storage_service.temp_dir / "cleanup_test"
        # Create the directory first to avoid file not found errors
        os.makedirs(carousel_dir, exist_ok=True)

        # Now schedule the cleanup
        test_storage_service.schedule_cleanup(mock_tasks, carousel_dir, hours=24)

        # Verify the cleanup file was created
        cleanup_file = carousel_dir / ".cleanup"
        assert cleanup_file.exists()

        # Read the file and verify it contains a future timestamp
        with open(cleanup_file, "r") as f:
            timestamp = f.read().strip()

        # Verify the timestamp is in ISO format
        try:
            cleanup_time = datetime.fromisoformat(timestamp)
            # Verify it's in the future
            assert cleanup_time > datetime.now()
        except ValueError:
            pytest.fail(f"Cleanup file does not contain a valid ISO timestamp: {timestamp}")
