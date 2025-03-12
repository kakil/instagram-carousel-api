import pytest
import json
from app import create_app


@pytest.fixture
def client():
    app = create_app("test")
    with app.test_client() as client:
        yield client


def test_health_check(client):
    """Test the health check endpoint"""
    response = client.get("/health")
    assert response.status_code == 200
    data = json.loads(response.data)
    assert data["status"] == "healthy"
    assert "timestamp" in data


def test_generate_carousel(client):
    """Test the carousel generation endpoint"""
    payload = {
        "carousel_title": "Test Carousel",
        "slides": [
            {"text": "This is slide one"},
            {"text": "This is slide two"}
        ],
        "include_logo": False
    }

    response = client.post(
        "/generate-carousel",
        data=json.dumps(payload),
        content_type="application/json"
    )

    assert response.status_code == 200
    data = json.loads(response.data)
    assert data["status"] == "success"
    assert "carousel_id" in data
    assert len(data["slides"]) == 2