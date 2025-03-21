"""
Main module for the Instagram Carousel Generator API.

This module provides the FastAPI application setup and server entry point.
"""

import logging
import os
import sys
from contextlib import asynccontextmanager
import uvicorn
from fastapi import FastAPI, Request
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import RedirectResponse, JSONResponse
from datetime import datetime

from app.core.config import settings
from app.services.storage_service import StorageService

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
    # Create the FastAPI app with proper configuration
    app = FastAPI(
        title=settings.PROJECT_NAME,
        description="API for generating Instagram carousel images with consistent styling",
        version="1.0.0",
        lifespan=lifespan,
    )

    # Configure CORS
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.ALLOW_ORIGINS,
        allow_credentials=settings.ALLOW_CREDENTIALS,
        allow_methods=settings.ALLOW_METHODS,
        allow_headers=settings.ALLOW_HEADERS,
    )

    # Middleware to ensure UTF-8 encoding for all responses
    @app.middleware("http")
    async def add_encoding_header(request: Request, call_next):
        response = await call_next(request)
        # Only set Content-Type for JSON responses to avoid interfering with other response types
        if response.headers.get("Content-Type", "").startswith("application/json"):
            response.headers["Content-Type"] = "application/json; charset=utf-8"
        return response

    # Mount static directories
    app.mount("/static", StaticFiles(directory=str(settings.STATIC_DIR)), name="static")

    # Health check endpoint
    @app.get("/health", tags=["health"])
    async def health_check():
        """Simple health check endpoint"""
        return {
            "status": "healthy",
            "timestamp": datetime.now().isoformat(),
            "version": "1.0.0",
        }

    # Redirect root to docs
    @app.get("/", include_in_schema=False)
    async def root():
        return RedirectResponse(url="/docs")

    # Include the API router with version prefix
    # We import here to avoid circular imports
    from app.api.endpoints import router as api_router
    app.include_router(api_router, prefix=settings.get_full_api_prefix())

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