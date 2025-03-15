from fastapi import FastAPI, Request
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
import uvicorn
from datetime import datetime
import os
from fastapi.responses import RedirectResponse, JSONResponse
from fastapi.openapi.docs import get_swagger_ui_html
import json

from starlette.responses import JSONResponse

from app.api.endpoints import router as api_router
from app.core.config import settings
from app.services import storage_service
from contextlib import asynccontextmanager


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup logic
    storage_service.cleanup_old_files()
    # ... any other startup logic you might have

    yield  # This is where the app runs

    # Shutdown logic
    # ... any shutdown logic you might have
    pass


# Create a main FastAPI app
# Get root_path from environment variable, or default to empty string
# for local development
ROOT_PATH = os.getenv("ROOT_PATH", "")


# Create your Instagram Carousel API app
app = FastAPI(
    title="Instagram Carousel Generator API",
    description="API for generating Instagram carousel images with consistent styling",
    version="1.0.0",
    root_path=ROOT_PATH,  # Set root_path for OpenAPI documentation
    default_response_class=JSONResponse,
    lifespan=lifespan,
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount static files
app.mount("/static", StaticFiles(directory="static"), name="static")
app.mount("/temp", StaticFiles(directory=storage_service.TEMP_DIR), name="temp")


# Add health check endpoint to the mounted app
@app.get("/health", tags=["health"])
async def health_check():
    """Simple health check endpoint"""
    return {
        "status": "healthy",
        "timestamp": datetime.now().isoformat()
    }

# Add logging
import logging
import sys
logging.basicConfig(stream=sys.stdout, level=logging.INFO)

# Add middleware for logging requests
# Add middleware to ensure UTF-8 encoding for all responses
@app.middleware("http")
async def add_encoding_header(request: Request, call_next):
    response = await call_next(request)
    # Only set Content-Type for JSON responses to avoid interfering with other response types
    if response.headers.get("Content-Type", "").startswith("application/json"):
        response.headers["Content-Type"] = "application/json; charset=utf-8"
    return response


# Custom JSON encoder to handle non-ASCII characters
class CustomJSONResponse(JSONResponse):
    def render(self, content: any) -> bytes:
        return json.dumps(
            content,
            ensure_ascii=False,
            allow_nan=False,
            indent=None,
            separators=(",", ":"),
        ).encode("utf-8")


# Use CustomJSONResponse for all responses by default
app.default_response_class = CustomJSONResponse

# Include the API router with the /api prefix
app.include_router(api_router, prefix=settings.API_PREFIX)


if __name__ == "__main__":
    uvicorn.run(
        "app.main:main_app",
        host="localhost",
        port=5001,
        reload=settings.DEBUG
    )