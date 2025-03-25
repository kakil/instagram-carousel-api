"""
Storage service for the Instagram Carousel Generator.

This module provides functionality for storing and managing carousel images.
"""
import logging
import os
import shutil
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Dict, List, Optional, Union

from fastapi import BackgroundTasks

from app.core.config import settings

logger = logging.getLogger(__name__)


class StorageService:
    """Service for managing temporary file storage and cleanup."""

    def __init__(self, temp_dir: Optional[Union[str, Path]] = None):
        """
        Initialize the storage service.

        Args:
            temp_dir: Path to the temporary directory (overrides default)
        """
        self.temp_dir = Path(temp_dir) if temp_dir is not None else Path(self._get_temp_dir())
        self.temp_dir.mkdir(parents=True, exist_ok=True)
        logger.info(f"Storage service initialized with temp_dir: {self.temp_dir}")

    def _get_temp_dir(self) -> str:
        """
        Get the temporary directory path from environment variables or configuration.

        Falls back to a local directory for development environments.
        """
        # First check settings
        if hasattr(settings, "TEMP_DIR") and settings.TEMP_DIR:
            return str(settings.TEMP_DIR)

        # Then check environment variable
        env_temp_dir = os.getenv("CAROUSEL_TEMP_DIR")
        if env_temp_dir:
            return env_temp_dir

        # If we're in production (check for some indicator in env)
        if os.getenv("PRODUCTION", "").lower() == "true":
            # Use the production path from environment or a sensible default
            return os.getenv("PRODUCTION_TEMP_DIR", str(settings.BASE_DIR / "static" / "temp"))

        # For development environment, use a local directory
        return str(settings.BASE_DIR / "static" / "temp")

    def save_carousel_images(
        self, carousel_id: str, images_data: List[Dict[str, Any]], base_url: str
    ) -> List[str]:
        """
        Save carousel images to temporary directory and return public URLs.

        Args:
            carousel_id: Unique identifier for the carousel
            images_data: List of dictionaries with image content and filenames
            base_url: Base URL for generating public URLs

        Returns:
            List of public URLs for the saved images
        """
        # Create directory for this carousel
        carousel_dir = self.temp_dir / carousel_id
        carousel_dir.mkdir(exist_ok=True)

        # Save images and generate URLs
        public_urls = []

        for image in images_data:
            try:
                # Decode hex content to binary
                binary_content = bytes.fromhex(image["content"])

                # Save to file
                file_path = carousel_dir / image["filename"]
                with open(file_path, "wb") as f:
                    f.write(binary_content)

                # Generate public URL using the API prefix from settings
                api_prefix = settings.get_full_api_prefix()
                public_url = (
                    f"{base_url.rstrip('/')}{api_prefix}/temp/{carousel_id}/{image['filename']}"
                )
                public_urls.append(public_url)

            except Exception as e:
                logger.error(f"Error saving image {image.get('filename', 'unknown')}: {str(e)}")
                # Continue with other images

        logger.info(f"Saved {len(public_urls)} images for carousel {carousel_id}")
        return public_urls

    def schedule_cleanup(
        self,
        background_tasks: BackgroundTasks,
        directory_path: Union[str, Path],
        hours: int = 24,
    ):
        """
        Schedule directory cleanup after specified hours.

        Args:
            background_tasks: FastAPI BackgroundTasks object
            directory_path: Path to directory to clean up
            hours: Number of hours after which to clean up
        """
        # Set a timestamp for cleanup
        try:
            directory_path = Path(directory_path)
            cleanup_file = directory_path / ".cleanup"
            with open(cleanup_file, "w") as f:
                cleanup_time = datetime.now() + timedelta(hours=hours)
                f.write(cleanup_time.isoformat())

            logger.info(f"Scheduled cleanup for {directory_path} in {hours} hours")
        except Exception as e:
            logger.error(f"Failed to schedule cleanup for {directory_path}: {e}")

    def cleanup_old_files(self, hours: Optional[int] = None):
        """
        Remove temporary files older than the specified or configured lifetime.

        Args:
            hours: Optional number of hours to use for determining file age.
                  If not provided, uses the configured lifetime from settings.
        """
        try:
            now = datetime.now()
            count = 0
            # Use provided hours or fall back to settings
            cleanup_hours = hours if hours is not None else settings.TEMP_FILE_LIFETIME_HOURS

            # Check all carousel directories
            for carousel_dir in os.listdir(self.temp_dir):
                dir_path = self.temp_dir / carousel_dir

                # Skip if not a directory
                if not dir_path.is_dir():
                    continue

                # Check for cleanup file
                cleanup_file = dir_path / ".cleanup"
                if cleanup_file.exists():
                    try:
                        with open(cleanup_file, "r") as f:
                            cleanup_time = datetime.fromisoformat(f.read().strip())

                        if now > cleanup_time:
                            shutil.rmtree(dir_path)
                            count += 1
                    except Exception as e:
                        logger.error(f"Error parsing cleanup file for {dir_path}: {e}")
                        # Fallback to modification time
                        file_modified = datetime.fromtimestamp(os.path.getmtime(dir_path))
                        if now - file_modified > timedelta(hours=cleanup_hours):
                            shutil.rmtree(dir_path)
                            count += 1
                else:
                    # No cleanup file, use modification time
                    file_modified = datetime.fromtimestamp(os.path.getmtime(dir_path))
                    if now - file_modified > timedelta(hours=cleanup_hours):
                        shutil.rmtree(dir_path)
                        count += 1

            if count > 0:
                logger.info(f"Cleaned up {count} expired carousel directories")

        except Exception as e:
            logger.error(f"Error cleaning up temporary files: {e}")

    def get_file_path(self, carousel_id: str, filename: str) -> Optional[Path]:
        """
        Get the file path for a carousel image.

        Args:
            carousel_id: Unique identifier for the carousel
            filename: Filename of the image

        Returns:
            Full path to the file or None if not found
        """
        file_path = self.temp_dir / carousel_id / filename
        if file_path.exists() and file_path.is_file():
            return file_path
        return None

    def get_content_type(self, filename: str) -> str:
        """
        Determine content type based on file extension.

        Args:
            filename: Name of the file

        Returns:
            MIME type for the file
        """
        lower_filename = filename.lower()
        if lower_filename.endswith(".png"):
            return "image/png"
        elif lower_filename.endswith(".jpg") or lower_filename.endswith(".jpeg"):
            return "image/jpeg"
        elif lower_filename.endswith(".gif"):
            return "image/gif"
        elif lower_filename.endswith(".webp"):
            return "image/webp"
        elif lower_filename.endswith(".svg"):
            return "image/svg+xml"
        else:
            return "application/octet-stream"


# Create a singleton instance for easy import
storage_service = StorageService()
