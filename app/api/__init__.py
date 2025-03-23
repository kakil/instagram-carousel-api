"""API package for Instagram Carousel Generator.

This package contains the API endpoints, routers, and security middleware.
"""

from fastapi import APIRouter
# Import the endpoints to register them with the router
from app.api.v1.endpoints import router as endpoints_router

# Create a router for the API endpoints
router = APIRouter()

# Include the endpoints router in the main router
router.include_router(endpoints_router)
