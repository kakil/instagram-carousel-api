"""
Storage service for the Instagram Carousel Generator.

This module provides functionality for storing and managing carousel images.
"""

import os
import shutil
import logging
from datetime import datetime, timedelta
import uuid
from fastapi import BackgroundTasks
from typing import List, Dict, Any, Optional
from pathlib import Path

from app.core.config import settings

logger = logging.getLogger(__name__)


class StorageService:
    """Service for managing temporary file storage and cleanup."""

    def __init__(self, temp_dir: Optional[str] = None):
        """
        Initialize the storage service.

        Args:
            temp_dir: Path to the temporary directory (overrides default)
        """
        self.temp_dir = temp_dir if temp_dir is not None else self._get_temp_dir()
        os.makedirs(self.temp_dir, exist_ok=True)
        logger.info(f"Storage service initialized with temp_dir: {self.temp_dir}")

    def _get_temp_dir(self) -> str:
        """
        Get the temporary directory path from environment variables or configuration.
        Falls back to a local directory for development environments.
        """
        # First check settings
        if hasattr(settings, 'TEMP_DIR') and settings.TEMP_DIR:
            return str(settings.TEMP_DIR)

        # Then check environment variable
        env_temp_dir = os.getenv("CAROUSEL_TEMP_DIR")
        if env_temp_dir:
            return env_temp_dir

        # If we're in production (check for some indicator in env)
        if os.getenv("PRODUCTION", "").lower() == "true":
            # Use the production path
            return "/var/www/api.kitwanaakil.com/public_html/instagram-carousel-api/static/temp"

        # For development environment, use a local directory
        # Get the absolute path to the directory containing this file
        base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        return os.path.join(base_dir, "static", "temp")

    def save_carousel_images(
            self,
            carousel_id: str,
            images_data: List[Dict[str, Any]],
            base_url: str
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
        carousel_dir = os.path.join(self.temp_dir, carousel_id)
        os.makedirs(carousel_dir, exist_ok=True)

        # Save images and generate URLs
        public_urls = []

        for image in images_data:
            try:
                # Decode hex content to binary
                binary_content = bytes.fromhex(image['content'])

                # Save to file
                file_path = os.path.join(carousel_dir, image['filename'])
                with open(file_path, 'wb') as f:
                    f.write(binary_content)

                # Generate public URL
                public_url = f"{base_url.rstrip('/')}/api/temp/{carousel_id}/{image['filename']}"
                public_urls.append(public_url)

            except Exception as e:
                logger.error(
                    f"Error saving image {image.get('filename', 'unknown')}: {str(e)}")
                # Continue with other images

        logger.info(f"Saved {len(public_urls)} images for carousel {carousel_id}")
        return public_urls

    def schedule_cleanup(
            self,
            background_tasks: BackgroundTasks,
            directory_path: str,
            hours: int = 24
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
            cleanup_file = os.path.join(directory_path, ".cleanup")
            with open(cleanup_file, 'w') as f:
                cleanup_time = datetime.now() + timedelta(hours=hours)
                f.write(cleanup_time.isoformat())

            logger.info(f"Scheduled cleanup for {directory_path} in {hours} hours")
        except Exception as e:
            logger.error(f"Failed to schedule cleanup for {directory_path}: {e}")

    def cleanup_old_files(self):
        """Remove temporary files older than 24 hours."""
        try:
            now = datetime.now()
            count = 0

            # Check all carousel directories
            for carousel_dir in os.listdir(self.temp_dir):
                dir_path = os.path.join(self.temp_dir, carousel_dir)

                # Skip if not a directory
                if not os.path.isdir(dir_path):
                    continue

                # Check for cleanup file
                cleanup_file = os.path.join(dir_path, ".cleanup")
                if os.path.exists(cleanup_file):
                    try:
                        with open(cleanup_file, 'r') as f:
                            cleanup_time = datetime.fromisoformat(f.read().strip())

                        if now > cleanup_time:
                            shutil.rmtree(dir_path)
                            count += 1
                    except Exception as e:
                        logger.error(
                            f"Error parsing cleanup file for {dir_path}: {e}")
                        # Fallback to modification time
                        file_modified = datetime.fromtimestamp(
                            os.path.getmtime(dir_path))
                        if now - file_modified > timedelta(hours=24):
                            shutil.rmtree(dir_path)
                            count += 1
                else:
                    # No cleanup file, use modification time
                    file_modified = datetime.fromtimestamp(
                        os.path.getmtime(dir_path))
                    if now - file_modified > timedelta(hours=24):
                        shutil.rmtree(dir_path)
                        count += 1

            if count > 0:
                logger.info(f"Cleaned up {count} expired carousel directories")

        except Exception as e:
            logger.error(f"Error cleaning up temporary files: {e}")

    def get_file_path(self, carousel_id: str, filename: str) -> Optional[str]:
        """
        Get the file path for a carousel image.

        Args:
            carousel_id: Unique identifier for the carousel
            filename: Filename of the image

        Returns:
            Full path to the file or None if not found
        """
        file_path = os.path.join(self.temp_dir, carousel_id, filename)
        if os.path.exists(file_path) and os.path.isfile(file_path):
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
        else:
            return "application/octet-stream"


# Create a singleton instance for easy import
storage_service = StorageService()