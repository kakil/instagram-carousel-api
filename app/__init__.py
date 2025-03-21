"""
Instagram Carousel Generator.

A FastAPI-based application for generating Instagram carousel images with consistent styling.
"""

__version__ = "1.0.0"
__author__ = "Your Name"

# Import key components for easier access
from app.core.config import settings


# We don't import create_app directly to avoid circular imports
# Instead, we'll provide a lazy import function
def get_app():
    from app.main import create_app
    return create_app()