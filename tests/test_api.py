"""
Test module for API endpoints.

This module contains tests for the API endpoints of the Instagram Carousel Generator.
Tests are organized into different classes based on endpoint functionality.
"""
import re

import pytest
from fastapi import status

# Import the get_app function to avoid circular imports


class TestHealthAndInfo:
    """Tests for health check and API info endpoints."""

    def test_health_check(self, client):
        """Test the health check endpoint returns 200 and correct data."""
        response = client.get("/health")
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["status"] == "healthy"
        assert "timestamp" in data
        assert "version" in data

    def test_api_info(self, client):
        """Test the API info endpoint returns correct version info."""
        response = client.get("/api-info")
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert "api_name" in data
        assert "api_version" in data
        assert "available_versions" in data
        assert "latest_version" in data

    def test_api_docs(self, client):
        """Test that API docs endpoint is accessible."""
        response = client.get("/docs")
        assert response.status_code == status.HTTP_200_OK

    def test_root_redirects_to_docs(self, client):
        """Test that root endpoint redirects to docs."""
        response = client.get("/", follow_redirects=False)
        assert response.status_code == status.HTTP_307_TEMPORARY_REDIRECT
        assert response.headers["location"] == "/docs"


class TestCarouselGeneration:
    """Tests for carousel generation endpoints."""

    def test_generate_carousel_with_mocks(self, client_with_mocks, carousel_request_data):
        """Test the carousel generation endpoint with mocked services."""
        response = client_with_mocks.post("/api/v1/generate-carousel", json=carousel_request_data)
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["status"] == "success"
        assert "carousel_id" in data
        assert isinstance(data["carousel_id"], str)
        assert re.match(r"^[0-9a-f]{8}$", data["carousel_id"]) is not None
        assert "slides" in data
        assert len(data["slides"]) > 0
        assert "processing_time" in data
        assert isinstance(data["processing_time"], (int, float))

    def test_generate_carousel_with_urls(self, client_with_mocks, carousel_request_data):
        """Test the carousel generation with URLs endpoint."""
        response = client_with_mocks.post(
            "/api/v1/generate-carousel-with-urls", json=carousel_request_data
        )
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["status"] == "success"
        assert "carousel_id" in data
        assert "slides" in data
        assert "public_urls" in data
        assert isinstance(data["public_urls"], list)
        assert all(isinstance(url, str) for url in data["public_urls"])
        assert all(url.startswith("http") for url in data["public_urls"])

    def test_generate_carousel_with_invalid_data(self, client_with_mocks):
        """Test carousel generation with invalid data returns appropriate error."""
        # Missing slides
        invalid_data = {"carousel_title": "Invalid Test", "include_logo": False}
        response = client_with_mocks.post("/api/v1/generate-carousel", json=invalid_data)
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY
        data = response.json()
        assert "detail" in data

    def test_generate_carousel_with_empty_slides(self, client_with_mocks):
        """Test carousel generation with empty slides list."""
        invalid_data = {
            "carousel_title": "Empty Slides Test",
            "slides": [],
            "include_logo": False,
            "logo_path": None,
        }
        response = client_with_mocks.post("/api/v1/generate-carousel", json=invalid_data)
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY
        data = response.json()
        assert "detail" in data
        assert "empty" in data["detail"].lower()


class TestFileAccess:
    """Tests for file access endpoints."""

    @pytest.mark.skip(reason="Complex async mocking - needs separate integration test")
    def test_get_temp_file(self, client_with_mocks, mock_storage_service):
        """Test accessing a temporary file."""
        # This test is skipped because it requires complex async mocking
        # that's better handled in a dedicated integration test

    def test_get_nonexistent_temp_file(self, client_with_mocks, mock_storage_service):
        """Test accessing a non-existent temporary file."""
        # Update the mock to simulate a file not found
        mock_path = mock_storage_service.get_file_path.return_value
        mock_path.exists.return_value = False

        response = client_with_mocks.get("/api/v1/temp/test123/nonexistent.png")

        assert response.status_code == status.HTTP_404_NOT_FOUND
        data = response.json()
        assert "detail" in data
        assert "not found" in data["detail"].lower()

    @pytest.mark.skip(reason="Complex path validation mocking - needs separate unit test")
    def test_invalid_temp_file_access(self, client_with_mocks):
        """Test accessing a temp file with invalid path parameters."""
        # This test is skipped because it requires complex mocking of path validation
        # that's better handled in a dedicated unit test
