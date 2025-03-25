"""
API router module for the Instagram Carousel Generator.

This module aggregates all versioned routers into a single router with versioned prefixes.
This creates a clean versioning structure that supports multiple API versions simultaneously.
"""
import logging

from fastapi import APIRouter, Depends, Request

# Import the v1 router (current version)
from app.api.v1.endpoints import router as router_v1

# Import the monitoring router
from app.api.v1.monitoring_endpoints import router as monitoring_router

# Set up logging
logger = logging.getLogger(__name__)

# Create the main API router that will include all versioned routers
api_router = APIRouter()

# Create tags for OpenAPI documentation
v1_tag = {
    "name": "v1",
    "description": "Version 1 API endpoints - Current stable version",
    "externalDocs": {
        "description": "API Versioning Documentation",
        "url": "/docs/api/versioning.md",
    },
}

monitoring_tag = {
    "name": "monitoring",
    "description": "Monitoring and metrics endpoints",
    "externalDocs": {
        "description": "Monitoring Documentation",
        "url": "/docs/guides/monitoring.md",
    },
}


# Function to add version information to request state
async def set_api_version(request: Request, version: str):
    """
    Dependency to set API version information in request state.

    This allows endpoints to know which version of the API they're being
    accessed through, which is useful for version-specific behavior.

    Args:
        request: The FastAPI request object
        version: API version string (e.g., "v1")
    """
    # Store version in request state
    request.state.api_version = version
    logger.debug(f"Request to API version: {version}")

    # No return value needed for dependencies that don't return a value
    return None


# Include each versioned router with its version prefix and appropriate tags
# Define a version-specific dependency function
def set_v1_api_version(request: Request):
    """Set API version to v1 in request state.

    This is a dependency function used to tag requests with the v1 API version.

    Args:
        request: The FastAPI request object

    Returns:
        The result of set_api_version with v1 as the version
    """
    return set_api_version(request, "v1")


api_router.include_router(
    router_v1, prefix="/v1", dependencies=[Depends(set_v1_api_version)], tags=["v1"]
)

# Include monitoring router without version prefix but with monitoring tag
api_router.include_router(
    monitoring_router, dependencies=[Depends(set_v1_api_version)], tags=["monitoring"]
)

# When new versions are added, they can be included like this:
# from app.api.v2.endpoints import router as router_v2
# api_router.include_router(
#     router_v2,
#     prefix="/v2",
#     dependencies=[Depends(lambda request: set_api_version(request, "v2"))],
#     tags=["v2"]
# )
