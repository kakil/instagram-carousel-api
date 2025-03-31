"""
Run script for the Instagram Carousel Generator API.

This module provides a convenient way to start the application
using uvicorn when executed directly as a script.
"""
import uvicorn

from app.core.config import settings

if __name__ == "__main__":
    uvicorn.run(
        "app.main:create_app",
        host=settings.HOST,
        port=settings.PORT,
        reload=settings.DEBUG,
        factory=True,
    )
