"""
Base image service module for the Instagram Carousel Generator.

This module provides the abstract base class and common functionality for
image service implementations, which handle the creation of carousel images
with consistent styling.
"""
import logging
import os
import tempfile
import time
import unicodedata
from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional, Tuple

from PIL import Image, ImageDraw, ImageFont

# Set up logging
logger = logging.getLogger(__name__)


class ImageServiceError(Exception):
    """Base exception class for image service errors."""


class ImageCreationError(ImageServiceError):
    """Exception raised when there's an error creating an image."""


class FontLoadError(ImageServiceError):
    """Exception raised when there's an error loading a font."""


class TextRenderingError(ImageServiceError):
    """Exception raised when there's an error rendering text."""


class BaseImageService(ABC):
    """
    Base abstract class for image service implementations.

    Defines the core interface and common utility methods.
    """

    def __init__(self, settings: Dict[str, Any] = None):
        """
        Initialize the image service with settings.

        Args:
            settings: Dictionary containing settings for image generation
        """
        self.settings = settings or {}
        self.default_width = self.settings.get("width", 1080)
        self.default_height = self.settings.get("height", 1080)
        self.default_bg_color = self.settings.get("bg_color", (18, 18, 18))
        self.default_font = self.settings.get("font", "Arial.ttf")
        self.default_font_bold = self.settings.get("font_bold", "Arial Bold.ttf")
        self.default_text_color = self.settings.get("text_color", (255, 255, 255))

    def sanitize_text(self, text: str) -> str:
        """
        Sanitize text by replacing or removing problematic Unicode characters.

        Args:
            text: The text to sanitize
        Returns:
            Sanitized text
        """
        if text is None:
            return ""
        # Convert to string if not already
        if not isinstance(text, str):
            text = str(text)
        # Replace specific problematic characters
        replacements = {
            "\u2192": "->",  # Right arrow
            "\u2190": "<-",  # Left arrow
            "\u2191": "^",  # Up arrow
            "\u2193": "v",  # Down arrow
            "\u2018": "'",  # Left single quote
            "\u2019": "'",  # Right single quote
            "\u201C": '"',  # Left double quote
            "\u201D": '"',  # Right double quote
            "\u2013": "-",  # En dash
            "\u2014": "-",  # Em dash
            "\u2026": "...",  # Ellipsis
        }
        for char, replacement in replacements.items():
            text = text.replace(char, replacement)
        # Normalize Unicode (NFKD = compatibility decomposition)
        text = unicodedata.normalize("NFKD", text)
        # Keep only ASCII characters if specified in settings
        if self.settings.get("ascii_only", False):
            text = "".join(c for c in text if ord(c) < 128)
        return text

    def safe_load_font(
        self, font_path: str, size: int, fallback_size: Optional[int] = None
    ) -> ImageFont.FreeTypeFont:
        """
        Safely load a font with fallbacks.

        Args:
            font_path: Path to the font file
            size: Desired font size
            fallback_size: Optional alternative size for fallback
        Returns:
            PIL ImageFont object
        Raises:
            FontLoadError: If font cannot be loaded
        """
        try:
            return ImageFont.truetype(font_path, size)
        except (IOError, OSError) as e:
            logger.warning(f"Could not load font {font_path} at size {size}: {e}")
            try:
                # Try loading a common system font
                for system_font in [
                    "Arial.ttf",
                    "DejaVuSans.ttf",
                    "FreeSans.ttf",
                    "LiberationSans-Regular.ttf",
                ]:
                    try:
                        return ImageFont.truetype(
                            system_font,
                            size if fallback_size is None else fallback_size,
                        )
                    except Exception as e:
                        logger.error(f"Error with text fallback {e}")
                        continue
                # If all else fails, use default
                return ImageFont.load_default()
            except Exception as e:
                logger.error(f"Failed to load any substitute font: {e}")
                return ImageFont.load_default()

    @abstractmethod
    def create_slide_image(
        self,
        title: str,
        text: str,
        slide_number: int,
        total_slides: int,
        include_logo: bool = False,
        logo_path: str = None,
    ) -> Image.Image:
        """
        Create an Instagram carousel slide with the specified styling.

        Args:
            title: Slide title (only shown on first slide)
            text: Main slide text content
            slide_number: Current slide number
            total_slides: Total number of slides
            include_logo: Whether to include a logo
            logo_path: Path to the logo file
        Returns:
            PIL Image object
        """

    @abstractmethod
    def create_gradient_text(
        self,
        draw: ImageDraw.Draw,
        text: str,
        position: Tuple[int, int],
        font,
        width: int,
        colors: List[Tuple[int, int, int]] = None,
    ) -> Tuple[Image.Image, Tuple[int, int]]:
        """
        Create gradient text from one color to another.

        Args:
            draw: ImageDraw object
            text: Text to render
            position: Center position (x, y) for the text
            font: Font to use
            width: Width of the image
            colors: List of (r, g, b) tuples for gradient start and end
        Returns:
            Tuple of (gradient_text_image, position)
        """

    @abstractmethod
    def create_error_slide(
        self, slide_number: int, total_slides: int, error_message: str
    ) -> Image.Image:
        """
        Create an error slide to display when there's a problem generating a slide.

        Args:
            slide_number: Current slide number
            total_slides: Total number of slides
            error_message: Error message to display
        Returns:
            PIL Image object
        """

    def create_carousel_images(
        self,
        carousel_title: str,
        slides_data: List[Dict[str, str]],
        carousel_id: str,
        include_logo: bool = False,
        logo_path: str = None,
    ) -> List[Dict[str, Any]]:
        """
        Create carousel images for Instagram based on text content.

        Args:
            carousel_title: The title for the carousel
            slides_data: List of dictionaries with slide text
            carousel_id: Unique identifier for the carousel
            include_logo: Whether to include a logo
            logo_path: Path to the logo file

        Returns:
            List of dictionaries with image data
        """
        # Start the timer for performance tracking
        start_time = time.time()
        logger.info(f"Beginning carousel generation for ID {carousel_id}")
        logger.info(f"Title: {carousel_title}")
        logger.info(f"Number of slides: {len(slides_data)}")

        # Create a temporary directory for the images
        with tempfile.TemporaryDirectory() as temp_dir:
            # Generate slides
            image_files = self._generate_all_slides(
                carousel_title,
                slides_data,
                carousel_id,
                include_logo,
                logo_path,
                temp_dir,
            )

            # Log performance metrics
            generation_time = time.time() - start_time
            logger.info(
                f"Carousel generation completed in {generation_time:.2f} seconds with "
                f"{len(image_files)} slides"
            )

            return image_files

    def _generate_all_slides(
        self,
        carousel_title: str,
        slides_data: List[Dict[str, str]],
        carousel_id: str,
        include_logo: bool,
        logo_path: str,
        temp_dir: str,
    ) -> List[Dict[str, Any]]:
        """Generate all slides for the carousel and store them in temporary directory."""
        image_files = []
        total_slides = len(slides_data)

        # Generate each slide
        for index, slide in enumerate(slides_data):
            slide_number = index + 1
            try:
                # Process this slide
                slide_result = self._process_single_slide(
                    carousel_title if index == 0 else None,
                    # Only show title on first slide
                    slide,
                    slide_number,
                    total_slides,
                    include_logo,
                    logo_path,
                    temp_dir,
                )
                image_files.append(slide_result)
                logger.info(f"Slide {slide_number} generated successfully")

            except Exception as e:
                # Handle errors per slide
                logger.error(f"Error processing slide {slide_number}: {str(e)}")
                error_result = self._create_error_slide_file(
                    index + 1, total_slides, str(e), temp_dir
                )
                image_files.append(error_result)
                logger.info(f"Error slide generated for slide {slide_number}")

        return image_files

    def _process_single_slide(
        self,
        title: Optional[str],
        slide: Dict[str, str],
        slide_number: int,
        total_slides: int,
        include_logo: bool,
        logo_path: str,
        temp_dir: str,
    ) -> Dict[str, Any]:
        """Process and generate a single carousel slide."""
        # Get slide text
        slide_text = slide.get("text", "")
        if not isinstance(slide_text, str):
            slide_text = str(slide_text)

        logger.info(f"Processing slide {slide_number}/{total_slides}")

        # Create image
        img = self.create_slide_image(
            title, slide_text, slide_number, total_slides, include_logo, logo_path
        )

        # Create result dictionary
        return self._save_slide_to_file(img, slide_number, temp_dir)

    def _create_error_slide_file(
        self, slide_number: int, total_slides: int, error_message: str, temp_dir: str
    ) -> Dict[str, Any]:
        """Create an error slide and save it to file."""
        # Create an error slide
        error_img = self.create_error_slide(slide_number, total_slides, error_message)

        # Save as error slide
        return self._save_slide_to_file(error_img, slide_number, temp_dir, is_error=True)

    def _save_slide_to_file(
        self, img: Image.Image, slide_number: int, temp_dir: str, is_error: bool = False
    ) -> Dict[str, Any]:
        """Save a slide image to file and return the metadata."""
        # Determine filename
        filename_suffix = "_error" if is_error else ""
        filename = f"slide_{slide_number}{filename_suffix}.png"

        # Save image
        filepath = os.path.join(temp_dir, filename)
        img.save(filepath)

        # Read file and convert to hex
        with open(filepath, "rb") as f:
            file_content = f.read()

        # Return metadata
        return {
            "filename": filename,
            "content": file_content.hex(),  # Convert binary to hex for JSON
        }
