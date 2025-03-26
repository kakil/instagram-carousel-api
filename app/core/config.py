"""
Configuration module for the Instagram Carousel Generator.

This module provides centralized configuration management using Pydantic's
BaseSettings, which allows for environment variable overrides and .env file loading.
"""
import json
import os
from pathlib import Path
from typing import Any, List, Optional, Tuple

from dotenv import load_dotenv
from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

# Load environment variables from .env file
load_dotenv()
# Get the base directory of the package
BASE_DIR = Path(__file__).resolve().parent.parent.parent
# Create logs directory if it doesn't exist
LOGS_DIR = BASE_DIR / "logs"
LOGS_DIR.mkdir(exist_ok=True)


class Settings(BaseSettings):
    """Application settings with comprehensive documentation."""

    # API settings
    API_PREFIX: str = Field(default="/api", description="API endpoint prefix")
    API_VERSION: str = Field(default="v1", description="API version")
    DEBUG: bool = Field(
        default_factory=lambda: os.getenv("DEBUG", "True") == "True",
        description="Debug mode",
    )
    PROJECT_NAME: str = Field(default="Instagram Carousel Generator", description="Project name")
    API_KEY: Optional[str] = Field(default=None, description="API key for authentication")

    # Public access settings
    PUBLIC_BASE_URL: str = Field(
        default_factory=lambda: os.getenv("PUBLIC_BASE_URL", "http://localhost:5001"),
        description="Base URL for public access to the API",
    )

    # Server settings
    HOST: str = Field(
        default_factory=lambda: os.getenv("HOST", "localhost"),
        description="Server host",
    )
    PORT: int = Field(
        default_factory=lambda: int(os.getenv("PORT", "5001")),
        description="Server port",
    )
    PRODUCTION: bool = Field(
        default_factory=lambda: os.getenv("PRODUCTION", "").lower() == "true",
        description="Flag indicating if the app is running in production mode",
    )

    # CORS settings
    # Change it to a simple hard-coded default:
    ALLOW_ORIGINS_STR: str = Field(
        default="*", description="Allowed CORS origins as comma-separated string"
    )
    ALLOW_CREDENTIALS: bool = Field(
        default_factory=lambda: os.getenv("ALLOW_CREDENTIALS", "True").lower() == "true",
        description="Allow credentials in CORS",
    )
    ALLOW_METHODS_STR: str = Field(default="*", description="Allowed HTTP methods in CORS")

    ALLOW_HEADERS_STR: str = Field(default="*", description="Allowed HTTP headers in CORS")

    # Security settings
    RATE_LIMIT_MAX_REQUESTS: int = Field(
        default_factory=lambda: int(os.getenv("RATE_LIMIT_MAX_REQUESTS", "100")),
        description="Maximum requests per window for rate limiting",
    )
    RATE_LIMIT_WINDOW_SECONDS: int = Field(
        default_factory=lambda: int(os.getenv("RATE_LIMIT_WINDOW_SECONDS", "60")),
        description="Time window for rate limiting in seconds",
    )
    ENABLE_HTTPS_REDIRECT: bool = Field(
        default_factory=lambda: os.getenv("ENABLE_HTTPS_REDIRECT", "False").lower() == "true",
        description="Redirect HTTP to HTTPS in production",
    )

    # Image generation settings
    DEFAULT_FONT: str = Field(
        default_factory=lambda: os.getenv("DEFAULT_FONT", "Arial.ttf"),
        description="Default font for text",
    )
    DEFAULT_FONT_BOLD: str = Field(
        default_factory=lambda: os.getenv("DEFAULT_FONT_BOLD", "Arial Bold.ttf"),
        description="Default bold font for titles",
    )
    DEFAULT_WIDTH: int = Field(
        default_factory=lambda: int(os.getenv("DEFAULT_WIDTH", "1080")),
        description="Default width for carousel images",
    )
    DEFAULT_HEIGHT: int = Field(
        default_factory=lambda: int(os.getenv("DEFAULT_HEIGHT", "1080")),
        description="Default height for carousel images",
    )
    DEFAULT_BG_COLOR: Tuple[int, int, int] = Field(
        default=(18, 18, 18), description="Default background color as RGB tuple"
    )

    # Instagram settings (optional for workflow automation)
    INSTAGRAM_ACCESS_TOKEN: Optional[str] = Field(
        default=None, description="Instagram Graph API access token"
    )
    INSTAGRAM_BUSINESS_ACCOUNT_ID: Optional[str] = Field(
        default=None, description="Instagram Business Account ID"
    )

    # Paths and directories
    BASE_DIR: Path = Field(default=BASE_DIR, description="Base directory of the application")
    STATIC_DIR: Path = Field(
        default_factory=lambda: BASE_DIR / "static",
        description="Static files directory",
    )
    ASSETS_DIR: Path = Field(
        default_factory=lambda: BASE_DIR / "static" / "assets",
        description="Assets directory",
    )
    TEMP_DIR: Path = Field(
        default_factory=lambda: BASE_DIR / "static" / "temp",
        description="Temporary files directory",
    )

    # Production paths
    PRODUCTION_TEMP_DIR: Path = Field(
        default_factory=lambda: Path(
            os.getenv(
                "PRODUCTION_TEMP_DIR",
                "/var/www/api.kitwanaakil.com/public_html/instagram-carousel-api/static/temp",
            )
        ),
        description="Path to temporary files directory in production",
    )

    # Storage settings
    TEMP_FILE_LIFETIME_HOURS: int = Field(
        default_factory=lambda: int(os.getenv("TEMP_FILE_LIFETIME_HOURS", "24")),
        description="Lifetime of temporary files in hours",
    )

    # Logging settings
    LOG_LEVEL: str = Field(
        default_factory=lambda: os.getenv("LOG_LEVEL", "INFO"),
        description="Logging level",
    )
    LOG_DIR: Path = Field(
        default_factory=lambda: Path(os.getenv("LOG_DIR", str(LOGS_DIR))),
        description="Directory for log files",
    )
    ENABLE_FILE_LOGGING: bool = Field(
        default_factory=lambda: os.getenv("ENABLE_FILE_LOGGING", "True").lower() == "true",
        description="Enable logging to files",
    )
    LOG_FORMAT_JSON: bool = Field(
        default_factory=lambda: os.getenv("LOG_FORMAT_JSON", "True").lower() == "true",
        description="Format logs as JSON (better for log aggregation)",
    )

    # Log Rotation Settings (optional, can be configured later)
    LOG_ROTATION_TYPE: str = Field(
        default_factory=lambda: os.getenv("LOG_ROTATION_TYPE", "size"),
        description="Log rotation type (size or time)",
    )
    LOG_MAX_SIZE: int = Field(
        default_factory=lambda: int(os.getenv("LOG_MAX_SIZE", "10485760")),  # 10MB default
        description="Maximum log file size in bytes for size-based rotation",
    )
    LOG_ROTATION_WHEN: str = Field(
        default_factory=lambda: os.getenv("LOG_ROTATION_WHEN", "D"),
        description="Time unit for time-based log rotation (S, M, H, D, W0-W6, midnight)",
    )
    LOG_ROTATION_INTERVAL: int = Field(
        default_factory=lambda: int(os.getenv("LOG_ROTATION_INTERVAL", "1")),
        description="Interval for time-based log rotation",
    )
    LOG_BACKUP_COUNT: int = Field(
        default_factory=lambda: int(os.getenv("LOG_BACKUP_COUNT", "30")),
        description="Number of backup log files to keep",
    )

    # Monitoring settings (disabled by default for now)
    ENABLE_MONITORING: bool = Field(
        default_factory=lambda: os.getenv("ENABLE_MONITORING", "False").lower() == "true",
        description="Enable monitoring features",
    )
    ENABLE_SYSTEM_METRICS: bool = Field(
        default_factory=lambda: os.getenv("ENABLE_SYSTEM_METRICS", "False").lower() == "true",
        description="Enable system metrics collection",
    )
    METRICS_COLLECTION_INTERVAL: int = Field(
        default_factory=lambda: int(os.getenv("METRICS_COLLECTION_INTERVAL", "60")),
        description="Interval in seconds for collecting system metrics",
    )
    ENABLE_PERFORMANCE_MONITORING: bool = Field(
        default_factory=lambda: os.getenv("ENABLE_PERFORMANCE_MONITORING", "False").lower()
        == "true",
        description="Enable performance monitoring",
    )

    # Use ConfigDict instead of Config class in Pydantic v2
    model_config = SettingsConfigDict(
        env_file=".env",
        case_sensitive=True,
        extra="ignore",  # This will ignore any extra fields in the environment
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

    # Replace the List[str] field with a simple string field
    ALLOW_ORIGINS_STR: str = Field(
        default="*", description="Allowed CORS origins as comma-separated string or wildcard"
    )

    # Remove the validator completely

    # Add this property to your Settings class
    # Add properties for all string-based CORS settings
    @property
    def ALLOW_ORIGINS(self) -> List[str]:
        """Parse ALLOW_ORIGINS_STR into a list of allowed origins."""
        return self._parse_cors_list(self.ALLOW_ORIGINS_STR)

    @property
    def ALLOW_METHODS(self) -> List[str]:
        """Parse ALLOW_METHODS_STR into a list of allowed methods."""
        return self._parse_cors_list(self.ALLOW_METHODS_STR)

    @property
    def ALLOW_HEADERS(self) -> List[str]:
        """Parse ALLOW_HEADERS_STR into a list of allowed headers."""
        return self._parse_cors_list(self.ALLOW_HEADERS_STR)

    def _parse_cors_list(self, value: str) -> List[str]:
        """Parse a CORS list value from string to list."""
        if not value or value.strip() == "":
            return []

        # Handle wildcard
        if value.strip() == "*":
            return ["*"]

        # Try parsing as JSON if it looks like JSON
        if value.strip().startswith("[") and value.strip().endswith("]"):
            try:
                parsed = json.loads(value)
                if isinstance(parsed, list):
                    return parsed
            except (json.JSONDecodeError, TypeError):
                pass

        # Split by comma and trim whitespace
        return [item.strip() for item in value.split(",") if item.strip()]

    def get_full_api_prefix(self) -> str:
        """Get the full API prefix with version."""
        return f"{self.API_PREFIX}/{self.API_VERSION}"


# Create a singleton settings instance
settings = Settings()
