from PIL import Image, ImageDraw, ImageFont
from typing import List, Dict, Any, Tuple, Optional
import os
import logging
import traceback
import unicodedata

from app.services.image_service.base_image_service import BaseImageService, \
    ImageCreationError, TextRenderingError

logger = logging.getLogger(__name__)


class EnhancedImageService(BaseImageService):
    """
    Enhanced implementation of the image service with advanced error handling,
    better text rendering, and more user-friendly error displays.
    This implementation is based on the production improved_image_service.py file.
    """

    def enhanced_sanitize_text(self, text: str) -> str:
        """
        Enhanced function to sanitize text by properly handling Unicode characters

        Args:
            text: The text to sanitize

        Returns:
            Sanitized text that can be safely rendered
        """
        if text is None:
            return ""

        # Convert to string if not already
        if not isinstance(text, str):
            text = str(text)

        # Apply text transformations in sequence
        text = self._replace_special_characters(text)
        text = self._normalize_unicode(text)
        text = self._handle_non_ascii_chars(text)

        return text

    def _replace_special_characters(self, text: str) -> str:
        """Replace specific problematic characters with safer alternatives"""
        replacements = {
            '\u2192': '->',  # Right arrow
            '\u2190': '<-',  # Left arrow
            '\u2191': '^',  # Up arrow
            '\u2193': 'v',  # Down arrow
            '\u2018': "'",  # Left single quote
            '\u2019': "'",  # Right single quote
            '\u201C': '"',  # Left double quote
            '\u201D': '"',  # Right double quote
            '\u2013': '-',  # En dash
            '\u2014': '-',  # Em dash
            '\u2026': '...',  # Ellipsis
            # Add more problematic characters as needed
        }

        for char, replacement in replacements.items():
            text = text.replace(char, replacement)

        return text

    def _normalize_unicode(self, text: str) -> str:
        """Normalize Unicode to canonical composition form"""
        return unicodedata.normalize('NFC', text)

    def _handle_non_ascii_chars(self, text: str) -> str:
        """Process non-ASCII characters with careful handling"""
        result = []
        for char in text:
            # Check if character is renderable or convert to a safe replacement
            try:
                # Encode and decode as ASCII to check if it's a simple character
                char.encode('ascii')
                result.append(char)
            except UnicodeEncodeError:
                # For non-ASCII characters, try to keep them if they're common
                # or replace with closest ASCII approximation if possible
                try:
                    # Test if Pillow can render this character with default font
                    # This is an indirect test by checking if it's a known Unicode category
                    if unicodedata.category(char)[
                        0] in 'LNPSZ':  # Letter, Number, Punctuation, Symbol, Separator
                        result.append(char)
                    else:
                        # Replace with '?' for unknown/uncommon categories
                        result.append('?')
                except:
                    # Fallback for any unexpected issues
                    result.append('?')

        return ''.join(result)

    def create_gradient_text(
            self,
            draw: ImageDraw.Draw,
            text: str,
            position: Tuple[int, int],
            font,
            width: int,
            colors: List[Tuple[int, int, int]] = None
    ) -> Tuple[Image.Image, Tuple[int, int]]:
        """
        Create gradient text from one color to another with improved error handling

        Args:
            draw: ImageDraw object
            text: Text to render
            position: Center position (x, y) for the text
            font: Font to use
            width: Width of the image
            colors: List of (r, g, b) tuples for gradient start and end

        Returns:
            tuple: (gradient_text_image, position)
        """
        # Apply text sanitization
        text = self.enhanced_sanitize_text(text)

        if not text:
            return self._create_empty_transparent_image(position)

        # Set default colors if not provided
        colors = colors or [(40, 100, 255),
                            (255, 255, 255)]  # Default blue to white gradient

        try:
            # Get text dimensions and create gradient text
            text_width, text_height = self._get_text_dimensions(draw, text,
                                                                font)

            # Create the gradient text image
            gradient_text = self._create_gradient_text_image(text, font,
                                                             text_width,
                                                             text_height,
                                                             colors)

            # Calculate centered position
            centered_position = self._calculate_centered_position(position,
                                                                  text_width,
                                                                  text_height)

            return gradient_text, centered_position

        except Exception as e:
            # Create fallback text if gradient fails
            return self._create_fallback_text(text, font, width, position)

    def _create_empty_transparent_image(self, position: Tuple[int, int]) -> \
    Tuple[Image.Image, Tuple[int, int]]:
        """Create an empty transparent image for empty text"""
        empty_img = Image.new("RGBA", (1, 1), color=(0, 0, 0, 0))
        return empty_img, position

    def _get_text_dimensions(self, draw: ImageDraw.Draw, text: str, font) -> \
    Tuple[int, int]:
        """Get the dimensions of the text with the given font"""
        text_bbox = draw.textbbox((0, 0), text, font=font)
        text_width = text_bbox[2] - text_bbox[0]
        text_height = text_bbox[3] - text_bbox[1]

        # Handle zero dimension cases
        if text_width <= 0 or text_height <= 0:
            text_width = max(text_width, 10)
            text_height = max(text_height, 10)

        return text_width, text_height

    def _create_gradient_text_image(
            self,
            text: str,
            font,
            text_width: int,
            text_height: int,
            colors: List[Tuple[int, int, int]]
    ) -> Image.Image:
        """Create a gradient text image with the given colors"""
        # Create a gradient mask
        gradient = self._create_gradient_mask(text_width, text_height, colors)

        # Create a transparent image for the text
        text_img = Image.new("RGBA", (text_width, text_height),
                             color=(0, 0, 0, 0))
        text_draw = ImageDraw.Draw(text_img)

        # Draw the text in white
        text_draw.text((0, 0), text, font=font, fill="white")

        # Apply the gradient mask to the text
        text_img.putalpha(gradient)

        return text_img

    def _create_gradient_mask(
            self,
            width: int,
            height: int,
            colors: List[Tuple[int, int, int]]
    ) -> Image.Image:
        """Create a gradient mask for text from left to right"""
        gradient = Image.new("L", (width, height), color=0)
        gradient_draw = ImageDraw.Draw(gradient)

        # Create gradient by drawing lines with increasing brightness
        for i in range(width):
            color_idx = i / width if width > 0 else 0
            r = int(colors[0][0] + color_idx * (colors[1][0] - colors[0][0]))
            g = int(colors[0][1] + color_idx * (colors[1][1] - colors[0][1]))
            b = int(colors[0][2] + color_idx * (colors[1][2] - colors[0][2]))
            brightness = int((r + g + b) / 3)
            gradient_draw.line([(i, 0), (i, height)], fill=brightness)

        return gradient

    def _calculate_centered_position(
            self,
            position: Tuple[int, int],
            text_width: int,
            text_height: int
    ) -> Tuple[int, int]:
        """Calculate the position to center the text"""
        x, y = position
        x = x - text_width // 2
        y = y - text_height // 2
        return x, y

    def _create_fallback_text(
            self,
            text: str,
            font,
            width: int,
            position: Tuple[int, int]
    ) -> Tuple[Image.Image, Tuple[int, int]]:
        """Create fallback text when gradient rendering fails"""
        logger.error(f"Error in create_gradient_text")

        # Create a simple fallback text image
        fallback_img = Image.new("RGBA", (width, 100), color=(0, 0, 0, 0))
        fallback_draw = ImageDraw.Draw(fallback_img)

        try:
            # Try to render simplified text
            simple_text = ''.join(c for c in text if
                                  c.isalnum() or c.isspace() or c in '.,!?-:;')
            fallback_draw.text((width // 2, 50),
                               simple_text or "[Text Rendering Error]",
                               font=font, fill="white", anchor="mm")
        except Exception:
            # Ultimate fallback
            fallback_draw.text((width // 2, 50), "[Text Rendering Error]",
                               font=font, fill="white", anchor="mm")

        return fallback_img, (0, position[1] - 50)

    def create_error_slide(
            self,
            slide_number: int,
            total_slides: int,
            error_message: str
    ) -> Image.Image:
        """
        Create an improved error slide with more helpful information

        Args:
            slide_number: Current slide number
            total_slides: Total number of slides
            error_message: Error message to display

        Returns:
            PIL Image object
        """
        # Extract the error slide creation into smaller focused methods
        width, height = self.default_width, self.default_height

        # Create the base slide with background
        img, draw = self._create_error_slide_base(width, height)

        # Load necessary fonts
        fonts = self._load_error_slide_fonts()

        # Add the error content to the slide
        self._add_error_title(draw, width, height, fonts['title'])

        # Add simplified error message
        simple_error = self._get_simplified_error_message(error_message)
        self._add_simple_error_message(draw, width, height, simple_error,
                                       fonts['body'])

        # Add detailed error message
        self._add_detailed_error_info(draw, width, height, error_message,
                                      fonts['small'])

        # Add help instruction
        self._add_error_instruction(draw, width, height, fonts['body'])

        # Add slide counter
        self._add_slide_counter(draw, slide_number, total_slides,
                                fonts['small'], width, height)

        # Add decorative elements
        self._add_decorative_elements(draw, width, height)

        return img

    def _create_error_slide_base(self, width: int, height: int) -> Tuple[
        Image.Image, ImageDraw.Draw]:
        """Create the base slide with background color"""
        img = Image.new("RGB", (width, height), (40, 40, 40))
        draw = ImageDraw.Draw(img)
        return img, draw

    def _load_error_slide_fonts(self) -> Dict[str, ImageFont.FreeTypeFont]:
        """Load fonts for the error slide with fallbacks"""
        return {
            'title': self.safe_load_font(
                self.settings.get('title_font', 'Arial Bold.ttf'), 48, 32),
            'body': self.safe_load_font(
                self.settings.get('text_font', 'Arial.ttf'), 32, 24),
            'small': self.safe_load_font(
                self.settings.get('nav_font', 'Arial.ttf'), 24, 18)
        }

    def _add_error_title(self, draw: ImageDraw.Draw, width: int, height: int,
                         font: ImageFont.FreeTypeFont):
        """Add error title to the slide"""
        title = "Error Creating Slide"
        text_position = (width // 2, height // 2 - 150)
        draw.text(text_position, title, fill=(255, 100, 100), anchor="mm",
                  font=font)

    def _get_simplified_error_message(self, error_message: str) -> str:
        """Get a simplified, user-friendly version of the error message"""
        if "codec can't encode character" in error_message:
            return "Unicode character issue"
        elif "cannot find font" in error_message.lower():
            return "Font loading error"
        elif "memory" in error_message.lower():
            return "Memory allocation error"
        return "Error processing text"

    def _add_simple_error_message(self, draw: ImageDraw.Draw, width: int,
                                  height: int,
                                  simple_error: str,
                                  font: ImageFont.FreeTypeFont):
        """Add simplified error message to the slide"""
        text_position = (width // 2, height // 2 - 70)
        draw.text(text_position, simple_error, fill=(240, 240, 240),
                  anchor="mm", font=font)

    def _add_detailed_error_info(self, draw: ImageDraw.Draw, width: int,
                                 height: int,
                                 error_message: str,
                                 font: ImageFont.FreeTypeFont):
        """Add detailed error information to the slide"""
        # Truncate error message if too long
        error_detail = error_message
        if len(error_detail) > 100:
            error_detail = error_detail[:97] + "..."

        # Wrap the error message text
        lines = self._wrap_error_text(error_detail)

        # Draw the wrapped text
        y_position = height // 2 + 20
        for line in lines:
            draw.text((width // 2, y_position), line, fill=(200, 200, 200),
                      anchor="mm", font=font)
            y_position += 30

    def _wrap_error_text(self, text: str) -> List[str]:
        """Wrap error text into multiple lines based on simple character count"""
        words = text.split()
        lines = []
        current_line = []

        for word in words:
            test_line = " ".join(current_line + [word])
            # Simple character count for line length
            if len(test_line) < 50:
                current_line.append(word)
            else:
                lines.append(" ".join(current_line))
                current_line = [word]

        if current_line:
            lines.append(" ".join(current_line))

        return lines

    def _add_error_instruction(self, draw: ImageDraw.Draw, width: int,
                               height: int,
                               font: ImageFont.FreeTypeFont):
        """Add helpful instruction to the error slide"""
        instruction = "Please check your text input for special characters"
        draw.text((width // 2, height // 2 + 150), instruction,
                  fill=(180, 180, 255), anchor="mm", font=font)

    def _add_decorative_elements(self, draw: ImageDraw.Draw, width: int,
                                 height: int):
        """Add decorative elements to the error slide"""
        # FIX: Use proper tuples instead of lists of tuples
        draw.rectangle(
            (width // 2 - 150, height // 2 - 180, width // 2 + 150,
             height // 2 - 180 + 4),
            fill=(255, 100, 100)
        )
        draw.rectangle(
            (width // 2 - 100, height // 2 + 180, width // 2 + 100,
             height // 2 + 180 + 4),
            fill=(180, 180, 255)
        )

    def create_slide_image(
            self,
            title: str,
            text: str,
            slide_number: int,
            total_slides: int,
            include_logo: bool = False,
            logo_path: str = None
    ) -> Image.Image:
        """
        Create an Instagram carousel slide with the specified styling

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
        # Get settings with defaults
        width = self.settings.get('width', self.default_width)
        height = self.settings.get('height', self.default_height)
        bg_color = self.settings.get('bg_color', self.default_bg_color)

        # Create the image
        image = Image.new("RGB", (width, height), bg_color)
        draw = ImageDraw.Draw(image)

        # Load fonts with improved error handling
        title_font = self.safe_load_font(
            self.settings.get('title_font', self.default_font_bold), 60, 48)
        text_font = self.safe_load_font(
            self.settings.get('text_font', self.default_font), 48, 36)
        navigation_font = self.safe_load_font(
            self.settings.get('nav_font', self.default_font), 36, 24)

        # Sanitize text content
        sanitized_title = self.enhanced_sanitize_text(title) if title else None
        sanitized_text = self.enhanced_sanitize_text(text)

        # Add each component to the image
        if sanitized_title:
            self._add_title_to_slide(image, draw, sanitized_title, title_font,
                                     width)

        if sanitized_text:
            self._add_text_to_slide(image, draw, sanitized_text, text_font,
                                    width, height)

        self._add_navigation_to_slide(draw, slide_number, total_slides,
                                      navigation_font, width, height)

        if include_logo and logo_path:
            self._add_logo_to_slide(image, logo_path, width, height,
                                    navigation_font)

        return image

    def _add_title_to_slide(self, image, draw, title, title_font, width):
        """Add the title with gradient effect to the slide"""
        try:
            # Create gradient text from blue to white for better visibility
            gradient_text, pos = self.create_gradient_text(
                draw,
                title,
                (width // 2, 150),
                title_font,
                width,
                [(40, 100, 255), (255, 255, 255)]  # Blue to white gradient
            )
            image.paste(gradient_text, pos, gradient_text)
        except Exception as e:
            logger.error(f"Error creating gradient title: {e}")
            logger.error(traceback.format_exc())
            # Fallback to plain text title
            try:
                text_bbox = draw.textbbox((0, 0), title, font=title_font)
                title_width = text_bbox[2] - text_bbox[0]
                draw.text((width // 2 - title_width // 2, 150),
                          title, fill="white", font=title_font)
            except:
                # Ultimate fallback for title
                draw.text((width // 2, 150), "[Title Error]", fill="white",
                          font=title_font, anchor="mm")

    def _add_text_to_slide(self, image, draw, text, text_font, width, height):
        """Add the main text to the slide with proper text wrapping"""
        # Split text into multiple lines for better layout
        lines = self._wrap_text(draw, text, text_font, width - 200)

        if not lines:
            lines = ["[Text rendering error]"]

        # Calculate start y position to center the text block
        line_height = 60
        total_text_height = len(lines) * line_height
        y_position = height / 2 - total_text_height / 2

        # Draw each line of text
        for line in lines:
            try:
                text_bbox = draw.textbbox((0, 0), line, font=text_font)
                text_width = text_bbox[2] - text_bbox[0]
                x_position = width / 2 - text_width / 2
                draw.text((x_position, y_position), line, fill="white",
                          font=text_font)
            except Exception as e:
                logger.error(f"Error rendering text line: {e}")
                # Fallback using anchor
                draw.text((width / 2, y_position), line, fill="white",
                          font=text_font, anchor="mt")

            y_position += line_height

    def _wrap_text(self, draw, text, font, max_width):
        """Wrap text to fit within the specified width"""
        words = text.split()
        lines = []
        current_line = []

        for word in words:
            test_line = " ".join(current_line + [word])
            text_bbox = draw.textbbox((0, 0), test_line, font=font)
            test_width = text_bbox[2] - text_bbox[0]

            # Check if adding this word exceeds the width
            if test_width < max_width:
                current_line.append(word)
            else:
                lines.append(" ".join(current_line))
                current_line = [word]

        if current_line:
            lines.append(" ".join(current_line))

        return lines

    def _add_navigation_to_slide(self, draw, slide_number, total_slides,
                                 navigation_font, width, height):
        """Add navigation arrows and slide counter to the slide"""
        # Add navigation arrows
        if slide_number > 1:
            try:
                draw.text((40, height / 2), "←", fill="white",
                          font=navigation_font)
            except:
                # Fallback for left arrow
                draw.text((40, height / 2), "<", fill="white",
                          font=navigation_font)

        if slide_number < total_slides:
            try:
                text_bbox = draw.textbbox((0, 0), "→", font=navigation_font)
                text_width = text_bbox[2] - text_bbox[0]
                draw.text((width - 40 - text_width, height / 2), "→",
                          fill="white", font=navigation_font)
            except:
                # Fallback for right arrow
                draw.text((width - 40, height / 2), ">", fill="white",
                          font=navigation_font)

        # Add slide counter with error handling
        self._add_slide_counter(draw, slide_number, total_slides,
                                navigation_font, width, height)

    def _add_slide_counter(self, draw, slide_number, total_slides,
                           navigation_font, width, height):
        """Add the slide counter to the slide"""
        counter_text = f"{slide_number}/{total_slides}"
        try:
            text_bbox = draw.textbbox((0, 0), counter_text,
                                      font=navigation_font)
            text_width = text_bbox[2] - text_bbox[0]
            text_height = text_bbox[3] - text_bbox[1]
            draw.text((width / 2 - text_width / 2, height - 60 - text_height),
                      counter_text, fill="white", font=navigation_font)
        except:
            # Fallback with simpler positioning
            draw.text((width / 2, height - 60), counter_text, fill="white",
                      font=navigation_font, anchor="mm")

    def _add_logo_to_slide(self, image, logo_path, width, height,
                           navigation_font):
        """Add logo to the slide if requested"""
        try:
            if os.path.exists(logo_path):
                logo = Image.open(logo_path).convert("RGBA")
                # Resize logo to be 10% of the image width
                logo_size = int(width * 0.1)
                # Use LANCZOS if available, otherwise fallback to ANTIALIAS
                resampling_method = Image.LANCZOS if hasattr(Image,
                                                             'LANCZOS') else Image.ANTIALIAS
                logo = logo.resize((logo_size, logo_size), resampling_method)

                # Position logo in bottom left corner with padding
                logo_position = (30, height - logo_size - 30)

                # Create a mask for the logo
                mask = logo.split()[3] if len(logo.split()) == 4 else None

                # Paste the logo onto the image
                image.paste(logo, logo_position, mask)
            else:
                logger.warning(f"Logo file not found: {logo_path}")
        except Exception as e:
            logger.error(f"Error adding logo: {e}")
            # Add error text instead of logo
            draw = ImageDraw.Draw(image)
            draw.text((60, height - 60), "Logo Error", fill=(255, 100, 100),
                      font=navigation_font)
