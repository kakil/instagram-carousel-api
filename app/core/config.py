from pydantic_settings import BaseSettings
from dotenv import load_dotenv
import os
from typing import Tuple

# Load environment variables from .env file
load_dotenv()


class Settings(BaseSettings):
    """Application settings"""
    API_PREFIX: str = "/api"
    DEBUG: bool = os.getenv("DEBUG", "True") == "True"
    PROJECT_NAME: str = "Instagram Carousel Generator"

    # Image generation settings
    DEFAULT_FONT: str = "Arial.ttf"
    DEFAULT_FONT_BOLD: str = "Arial Bold.ttf"
    DEFAULT_WIDTH: int = 1080
    DEFAULT_HEIGHT: int = 1080
    DEFAULT_BG_COLOR: Tuple[int, int, int] = (18, 18, 18)  # Dark background

    # Default assets directory
    ASSETS_DIR: str = "static/assets"

    class Config:
        case_sensitive = True


settings = Settings()