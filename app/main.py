from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
import uvicorn
from datetime import datetime

from app.api.endpoints import router as api_router
from app.core.config import settings

app = FastAPI(
    title="Instagram Carousel Generator API",
    description="API for generating Instagram carousel images with consistent styling",
    version="1.0.0"
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

# Add health check endpoint
@app.get("/health", tags=["health"])
async def health_check():
    """Simple health check endpoint"""
    return {
        "status": "healthy",
        "timestamp": datetime.now().isoformat()
    }

# Include API router
app.include_router(api_router, prefix="/api")

if __name__ == "__main__":
    uvicorn.run(
        "app.main:app",
        host="localhost",
        port=5001,
        reload=settings.DEBUG
    )