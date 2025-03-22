"""API package for Instagram Carousel Generator.

This package contains the API endpoints, routers, and security middleware.
"""

from fastapi import APIRouter

# Create a router for the API endpoints
router = APIRouter()

# Import the endpoints to register them with the router
from app.api.endpoints import router as endpoints_router

# Include the endpoints router in the main router
router.include_router(endpoints_router)