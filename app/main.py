from fastapi import FastAPI, Request
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
import uvicorn
from datetime import datetime
import os
from fastapi.responses import RedirectResponse
from fastapi.openapi.docs import get_swagger_ui_html


from app.api.endpoints import router as api_router
from app.core.config import settings

# Create a main FastAPI app
# Get root_path from environment variable, or default to empty string for local development
ROOT_PATH = os.getenv("ROOT_PATH", "")


# Create your Instagram Carousel API app
app = FastAPI(
    title="Instagram Carousel Generator API",
    description="API for generating Instagram carousel images with consistent styling",
    version="1.0.0",
    root_path=ROOT_PATH  # Set root_path for OpenAPI documentation
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

# Add health check endpoint to the mounted app
@app.get("/health", tags=["health"])
async def health_check():
    """Simple health check endpoint"""
    return {
        "status": "healthy",
        "timestamp": datetime.now().isoformat()
    }

# Include the API router with the /api prefix
app.include_router(api_router, prefix=settings.API_PREFIX)


if __name__ == "__main__":
    uvicorn.run(
        "app.main:main_app",
        host="localhost",
        port=5001,
        reload=settings.DEBUG
    )