"""
Configuration module for the Instagram Carousel Generator.

This module provides centralized configuration management using Pydantic's
BaseSettings, which allows for environment variable overrides and .env file loading.
"""

from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import Field, field_validator
from dotenv import load_dotenv
import os
from typing import Tuple, Optional, List, Any
from pathlib import Path

# Load environment variables from .env file
load_dotenv()

# Get the base directory of the package
BASE_DIR = Path(__file__).resolve().parent.parent.parent


class Settings(BaseSettings):
    """Application settings with comprehensive documentation."""

    # API settings
    API_PREFIX: str = Field(default="/api", description="API endpoint prefix")
    API_VERSION: str = Field(default="v1", description="API version")
    DEBUG: bool = Field(default_factory=lambda: os.getenv("DEBUG", "True") == "True", description="Debug mode")
    PROJECT_NAME: str = Field(default="Instagram Carousel Generator", description="Project name")
    API_KEY: Optional[str] = Field(default=None, description="API key for authentication")

    # Public access settings
    PUBLIC_BASE_URL: str = Field(
        default_factory=lambda: os.getenv("PUBLIC_BASE_URL", "http://localhost:5001"),
        description="Base URL for public access to the API"
    )

    # Server settings
    HOST: str = Field(default_factory=lambda: os.getenv("HOST", "localhost"), description="Server host")
    PORT: int = Field(default_factory=lambda: int(os.getenv("PORT", "5001")), description="Server port")
    PRODUCTION: bool = Field(
        default_factory=lambda: os.getenv("PRODUCTION", "").lower() == "true",
        description="Flag indicating if the app is running in production mode"
    )

    # CORS settings
    ALLOW_ORIGINS: List[str] = Field(default=["*"], description="Allowed CORS origins")
    ALLOW_CREDENTIALS: bool = Field(default=True, description="Allow credentials in CORS")
    ALLOW_METHODS: List[str] = Field(default=["*"], description="Allowed HTTP methods in CORS")
    ALLOW_HEADERS: List[str] = Field(default=["*"], description="Allowed HTTP headers in CORS")

    # Image generation settings
    DEFAULT_FONT: str = Field(
        default_factory=lambda: os.getenv("DEFAULT_FONT", "Arial.ttf"),
        description="Default font for text"
    )
    DEFAULT_FONT_BOLD: str = Field(
        default_factory=lambda: os.getenv("DEFAULT_FONT_BOLD", "Arial Bold.ttf"),
        description="Default bold font for titles"
    )
    DEFAULT_WIDTH: int = Field(
        default_factory=lambda: int(os.getenv("DEFAULT_WIDTH", "1080")),
        description="Default width for carousel images"
    )
    DEFAULT_HEIGHT: int = Field(
        default_factory=lambda: int(os.getenv("DEFAULT_HEIGHT", "1080")),
        description="Default height for carousel images"
    )
    DEFAULT_BG_COLOR: Tuple[int, int, int] = Field(
        default=(18, 18, 18),
        description="Default background color as RGB tuple"
    )

    # Instagram settings (optional for workflow automation)
    INSTAGRAM_ACCESS_TOKEN: Optional[str] = Field(
        default=None,
        description="Instagram Graph API access token"
    )
    INSTAGRAM_BUSINESS_ACCOUNT_ID: Optional[str] = Field(
        default=None,
        description="Instagram Business Account ID"
    )

    # Paths and directories
    BASE_DIR: Path = Field(default=BASE_DIR, description="Base directory of the application")
    STATIC_DIR: Path = Field(default_factory=lambda: BASE_DIR / "static", description="Static files directory")
    ASSETS_DIR: Path = Field(default_factory=lambda: BASE_DIR / "static" / "assets", description="Assets directory")
    TEMP_DIR: Path = Field(default_factory=lambda: BASE_DIR / "static" / "temp", description="Temporary files directory")

    # Production paths
    PRODUCTION_TEMP_DIR: Path = Field(
        default_factory=lambda: Path(os.getenv(
            "PRODUCTION_TEMP_DIR",
            "/var/www/api.kitwanaakil.com/public_html/instagram-carousel-api/static/temp"
        )),
        description="Path to temporary files directory in production"
    )

    # Storage settings
    TEMP_FILE_LIFETIME_HOURS: int = Field(
        default_factory=lambda: int(os.getenv("TEMP_FILE_LIFETIME_HOURS", "24")),
        description="Lifetime of temporary files in hours"
    )

    # Logging settings
    LOG_LEVEL: str = Field(
        default_factory=lambda: os.getenv("LOG_LEVEL", "INFO"),
        description="Logging level"
    )

    # Use ConfigDict instead of Config class in Pydantic v2
    model_config = SettingsConfigDict(
        env_file=".env",
        case_sensitive=True,
        extra="ignore"  # This will ignore any extra fields in the environment
    )

    @field_validator("DEFAULT_BG_COLOR", mode="before")
    def parse_bg_color(cls, v: Any) -> Tuple[int, int, int]:
        """Parse background color from environment variables if not already a tuple."""
        if isinstance(v, tuple) and len(v) == 3:
            return v

        try:
            r = int(os.getenv("DEFAULT_BG_COLOR_R", "18"))
            g = int(os.getenv("DEFAULT_BG_COLOR_G", "18"))
            b = int(os.getenv("DEFAULT_BG_COLOR_B", "18"))
            return (r, g, b)
        except (ValueError, TypeError):
            return (18, 18, 18)  # Default fallback

    def get_full_api_prefix(self) -> str:
        """Get the full API prefix with version."""
        return f"{self.API_PREFIX}/{self.API_VERSION}"


# Create a singleton settings instance
settings = Settings()