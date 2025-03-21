"""
Test module for API endpoints.
"""

import pytest
import json
from fastapi.testclient import TestClient

# Import the get_app function to avoid circular imports
from app import get_app


def test_health_check(client):
    """Test the health check endpoint"""
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert "timestamp" in data


def test_api_docs():
    """Test that API docs endpoint is accessible"""
    app = get_app()
    client = TestClient(app)
    response = client.get("/docs")
    assert response.status_code == 200


@pytest.mark.skip(reason="Requires more setup with test data")
def test_generate_carousel(client, test_image):
    """Test the carousel generation endpoint"""
    response = client.post(
        "/api/v1/generate-carousel",
        json=test_image
    )

    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "success"
    assert "carousel_id" in data
    assert len(data["slides"]) == 2