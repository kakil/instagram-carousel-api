"""
Main module for the Instagram Carousel Generator API.

This module provides the FastAPI application setup and server entry point.
"""

import logging
import os
import sys
from contextlib import asynccontextmanager
import uvicorn
from fastapi import FastAPI, Request, Depends
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import RedirectResponse, JSONResponse
from datetime import datetime
import time

from app.core.config import settings
from app.services.storage_service import StorageService
from app.api.security import get_api_key, rate_limit, validate_file_access

# Configure logging
logging.basicConfig(
    level=getattr(logging, settings.LOG_LEVEL),
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[
        logging.StreamHandler(sys.stdout),
    ],
)

logger = logging.getLogger(__name__)

# Initialize storage service
storage_service = StorageService()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Lifecycle hooks for the FastAPI application.

    Args:
        app: The FastAPI application
    """
    # Startup logic
    logger.info("Starting Instagram Carousel Generator API")
    
    # Initialize the dependency injection system
    from app.core.services_setup import register_services
    register_services()
    logger.info("Service registry initialized")
    
    # Clean up old files
    storage_service.cleanup_old_files()

    yield  # This is where the app runs

    # Shutdown logic
    logger.info("Shutting down Instagram Carousel Generator API")


def create_app() -> FastAPI:
    """
    Create and configure the FastAPI application.

    Returns:
        Configured FastAPI application
    """
    # Initialize the dependency injection system
    from app.core.services_setup import register_services
    register_services()
    
    # Create the FastAPI app with proper configuration
    app = FastAPI(
        title=settings.PROJECT_NAME,
        description="""
        API for generating Instagram carousel images with consistent styling.
        
        ## API Versioning
        
        This API uses URL-based versioning (e.g., `/api/v1/...`). 
        Always include the version in your API requests to ensure compatibility.
        
        - Current version: v1
        - For more information about versioning, see the `/api-info` endpoint or visit our [API Versioning Guide](/docs#section/Versioning).
        
        ## Dependency Injection
        
        This API uses dependency injection for service management, which makes components more
        modular, testable, and extensible. See our dependency injection guide in the documentation
        for more details.
        """,
        version="1.0.0",
        lifespan=lifespan,
    )

    # Configure CORS with more restrictive settings in production
    # In production, restrict origins to your specific domains
    origins = settings.ALLOW_ORIGINS
    if settings.PRODUCTION and origins == ["*"]:
        logger.warning("Using wildcard CORS origin in production. Consider restricting origins.")

    app.add_middleware(
        CORSMiddleware,
        allow_origins=origins,
        allow_credentials=settings.ALLOW_CREDENTIALS,
        allow_methods=settings.ALLOW_METHODS,
        allow_headers=settings.ALLOW_HEADERS,
    )

    # Add the API version middleware
    from app.api.middleware import version_middleware

    @app.middleware("http")
    async def api_version_middleware(request: Request, call_next):
        """Middleware for managing API versioning notices"""
        return await version_middleware(request, call_next)

    # Middleware to ensure UTF-8 encoding for all responses
    @app.middleware("http")
    async def add_encoding_header(request: Request, call_next):
        response = await call_next(request)
        # Only set Content-Type for JSON responses to avoid interfering with other response types
        if response.headers.get("Content-Type", "").startswith("application/json"):
            response.headers["Content-Type"] = "application/json; charset=utf-8"
        return response

    # Middleware for request logging and timing
    @app.middleware("http")
    async def log_requests(request: Request, call_next):
        start_time = time.time()

        # Get client info safely
        client_host = request.client.host if request.client else "unknown"

        # Process the request
        response = await call_next(request)

        # Calculate processing time
        process_time = time.time() - start_time

        # Log request details
        logger.info(
            f"Request: {request.method} {request.url.path} | " 
            f"Client: {client_host} | "
            f"Status: {response.status_code} | "
            f"Time: {process_time:.3f}s"
        )

        # Add timing header
        response.headers["X-Process-Time"] = str(process_time)

        return response

    # Mount static directories
    app.mount("/static", StaticFiles(directory=str(settings.STATIC_DIR)), name="static")

    # Health check endpoint (no authentication required)
    @app.get("/health", tags=["health"])
    async def health_check():
        """Simple health check endpoint"""
        return {
            "status": "healthy",
            "timestamp": datetime.now().isoformat(),
            "version": "1.0.0",
            "api_version": "v1",
        }

    @app.get("/api-info", tags=["versioning"])
    async def api_info():
        """Get API version information"""
        from app.api.middleware import get_all_versions, get_latest_version

        return {
            "api_name": settings.PROJECT_NAME,
            "api_version": "1.0.0",
            "available_versions": get_all_versions(),
            "latest_version": get_latest_version(),
            "documentation_url": f"{settings.PUBLIC_BASE_URL}/docs",
        }

    # Redirect root to docs
    @app.get("/", include_in_schema=False)
    async def root():
        return RedirectResponse(url="/docs")

    # Include the versioned API router
    from app.api.router import api_router

    # Apply API key security to all API endpoints
    # Public endpoints like health check are defined directly in this file
    app.include_router(
        api_router,
        prefix=settings.API_PREFIX,  # Only use the prefix without version
        dependencies=[Depends(get_api_key), Depends(rate_limit())]
    )

    return app


def run_app():
    """Run the FastAPI application with uvicorn."""
    app = create_app()
    uvicorn.run(
        "app.main:create_app",
        host=settings.HOST,
        port=settings.PORT,
        reload=settings.DEBUG,
        factory=True,
    )


# For direct execution
if __name__ == "__main__":
    run_app()