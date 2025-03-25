"""
Test server for the Instagram Carousel Generator API.

This module creates a simple FastAPI server that tests if core imports
from the Instagram Carousel Generator API package are working correctly.
It's used for diagnostic purposes during development and deployment.
"""
from datetime import datetime

import uvicorn
from fastapi import FastAPI

# Try importing from your app package
try:
    from app.core.config import settings  # noqa: F401 - Used for testing imports

    config_import_success = True
except Exception as e:
    config_import_success = False
    config_error = str(e)

# Add this to the imports section in server.py
try:
    from app.api.v1.endpoints import router as api_router  # noqa: F401 - Used for testing imports

    router_import_success = True
except Exception as e:
    router_import_success = False
    router_error = str(e)

app = FastAPI(
    title="Instagram Carousel Generator API - Test",
    description="Testing imports from app package",
    version="1.0.0",
)


@app.get("/health", tags=["health"])
async def health_check():
    """Check API health and import status of core modules."""
    return {
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "config_import": config_import_success,
        "router_import": router_import_success,
        "config_error": config_error if not config_import_success else None,
        "router_error": router_error if not router_import_success else None,
    }


if __name__ == "__main__":
    uvicorn.run("server:app", host="0.0.0.0", port=5001, reload=True)
