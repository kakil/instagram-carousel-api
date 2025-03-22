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
from app.api.security import get_api_key, rate_limit

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
        docs_url=None if settings.PRODUCTION else "/docs",  # Hide docs in production
        redoc_url=None if settings.PRODUCTION else "/redoc",  # Hide redoc in production
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

    # Security headers middleware for all responses
    @app.middleware("http")
    async def add_security_headers(request: Request, call_next):
        response = await call_next(request)

        # Add security headers
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-XSS-Protection"] = "1; mode=block"

        # Only add HSTS header in production and for HTTPS requests
        if settings.PRODUCTION and not request.url.scheme == "http":
            response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"

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
        }

    # Redirect root to docs in development, or a simple message in production
    @app.get("/", include_in_schema=False)
    async def root():
        if settings.PRODUCTION:
            return {"message": "Instagram Carousel Generator API"}
        else:
            return RedirectResponse(url="/docs")

    # Include the API router with version prefix and security dependency
    from app.api.endpoints import router as api_router

    # Apply API key security and rate limiting to all API endpoints
    # Public endpoints like health check are defined directly in this file
    app.include_router(
        api_router,
        prefix=settings.get_full_api_prefix(),
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