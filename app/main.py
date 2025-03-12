from fastapi import FastAPI, Request
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
import uvicorn
from datetime import datetime
from fastapi.responses import RedirectResponse

from app.api.endpoints import router as api_router
from app.core.config import settings

# Create a main FastAPI app
main_app = FastAPI()

# Create your Instagram Carousel API app
app = FastAPI(
    title="Instagram Carousel Generator API",
    description="API for generating Instagram carousel images with consistent styling",
    version="1.0.0",
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

# Add test endpoint to mounted app
@app.get("/test")
async def app_test():
    return {"message": "Mounted app is working correctly"}

# Root endpoint for the mounted app
@app.get("/")
async def app_root():
    return {"message": "Instagram Carousel API root"}

# Include API router in the mounted app
app.include_router(api_router, prefix="/api")

# Mount the app at /instagram-carousel
main_app.mount("/instagram-carousel", app)

# Add a root path redirect for convenience on the main app
@main_app.get("/")
async def redirect_to_docs():
    return RedirectResponse(url="/instagram-carousel/docs")

# Add test endpoint to main app
@main_app.get("/test")
async def main_test():
    return {"message": "Main app is working correctly"}

# Debug endpoint on the main app
@main_app.get("/debug")
async def debug():
    """Debug endpoint to help troubleshoot routing issues"""
    return {
        "routes": [
            {"path": route.path, "name": route.name}
            for route in main_app.routes
        ]
    }

if __name__ == "__main__":
    uvicorn.run(
        "app.main:main_app",
        host="localhost",
        port=5001,
        reload=settings.DEBUG
    )