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

        # Replace specific problematic characters that might cause rendering issues
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

        # First, try NFC normalization (canonical composition)
        text = unicodedata.normalize('NFC', text)

        # Then do a safer approach that attempts to preserve as much as possible
        # while removing characters that can't be rendered
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
            # Return empty transparent image if text is empty
            empty_img = Image.new("RGBA", (1, 1), color=(0, 0, 0, 0))
            return empty_img, position

        if colors is None:
            # Default blue to white gradient instead of black to white
            colors = [(40, 100, 255), (255, 255, 255)]

        try:
            # Get text size
            text_bbox = draw.textbbox((0, 0), text, font=font)
            text_width = text_bbox[2] - text_bbox[0]
            text_height = text_bbox[3] - text_bbox[1]

            if text_width <= 0 or text_height <= 0:
                # Handle zero dimension cases
                text_width = max(text_width, 10)
                text_height = max(text_height, 10)

            # Create a gradient mask
            gradient = Image.new("L", (text_width, text_height), color=0)
            gradient_draw = ImageDraw.Draw(gradient)

            # Create gradient by drawing lines with increasing brightness
            for i in range(text_width):
                color_idx = i / text_width if text_width > 0 else 0
                r = int(
                    colors[0][0] + color_idx * (colors[1][0] - colors[0][0]))
                g = int(
                    colors[0][1] + color_idx * (colors[1][1] - colors[0][1]))
                b = int(
                    colors[0][2] + color_idx * (colors[1][2] - colors[0][2]))
                brightness = int((r + g + b) / 3)
                gradient_draw.line([(i, 0), (i, text_height)], fill=brightness)

            # Create a transparent image for the text
            text_img = Image.new("RGBA", (text_width, text_height),
                                 color=(0, 0, 0, 0))
            text_draw = ImageDraw.Draw(text_img)

            # Draw the text in white
            text_draw.text((0, 0), text, font=font, fill="white")

            # Apply the gradient mask to the text
            text_img.putalpha(gradient)

            # Calculate position to center the text
            x, y = position
            x = x - text_width // 2
            y = y - text_height // 2

            return text_img, (x, y)

        except Exception as e:
            logger.error(f"Error in create_gradient_text: {e}")
            logger.error(traceback.format_exc())

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
            except:
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
            width: Image width
            height: Image height

        Returns:
            PIL Image object
        """
        width, height = self.default_width, self.default_height

        # Create dark gray background
        img = Image.new("RGB", (width, height), (40, 40, 40))
        draw = ImageDraw.Draw(img)

        # Try to load fonts with fallbacks
        title_font = self.safe_load_font(
            self.settings.get('title_font', 'Arial Bold.ttf'), 48, 32)
        body_font = self.safe_load_font(
            self.settings.get('text_font', 'Arial.ttf'), 32, 24)
        small_font = self.safe_load_font(
            self.settings.get('nav_font', 'Arial.ttf'), 24, 18)

        # Error title
        title = "Error Creating Slide"
        text_position = (width // 2, height // 2 - 150)
        draw.text(text_position, title, fill=(255, 100, 100), anchor="mm",
                  font=title_font)

        # Simplified error message
        simple_error = "Error processing text"
        if "codec can't encode character" in error_message:
            simple_error = "Unicode character issue"
        elif "cannot find font" in error_message.lower():
            simple_error = "Font loading error"
        elif "memory" in error_message.lower():
            simple_error = "Memory allocation error"

        # Add technical information in smaller text
        text_position = (width // 2, height // 2 - 70)
        draw.text(text_position, simple_error, fill=(240, 240, 240),
                  anchor="mm", font=body_font)

        # Add more detailed error info
        error_detail = error_message
        if len(error_detail) > 100:
            error_detail = error_detail[:97] + "..."

        text_position = (width // 2, height // 2)

        # Split long error message into multiple lines
        words = error_detail.split()
        lines = []
        current_line = []

        for word in words:
            test_line = " ".join(current_line + [word])
            # Check if adding this word exceeds the width
            if len(test_line) < 50:  # Simple character count for line length
                current_line.append(word)
            else:
                lines.append(" ".join(current_line))
                current_line = [word]

        if current_line:
            lines.append(" ".join(current_line))

        # Draw each line of text
        y_position = height // 2 + 20
        for line in lines:
            draw.text((width // 2, y_position), line, fill=(200, 200, 200),
                      anchor="mm", font=small_font)
            y_position += 30

        # Add instruction
        instruction = "Please check your text input for special characters"
        draw.text((width // 2, height // 2 + 150), instruction,
                  fill=(180, 180, 255), anchor="mm", font=body_font)

        # Add slide counter
        counter_text = f"{slide_number}/{total_slides}"
        counter_position = (width // 2, height - 50)
        draw.text(counter_position, counter_text, fill="white", anchor="mm",
                  font=small_font)

        # Add decorative elements
        draw.rectangle([(width // 2 - 150, height // 2 - 180),
                        (width // 2 + 150, height // 2 - 180 + 4)],
                       fill=(255, 100, 100))
        draw.rectangle([(width // 2 - 100, height // 2 + 180),
                        (width // 2 + 100, height // 2 + 180 + 4)],
                       fill=(180, 180, 255))

        return img

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

        # Add title with gradient effect (only on first slide)
        if sanitized_title:
            try:
                # Create gradient text from blue to white for better visibility
                gradient_text, pos = self.create_gradient_text(
                    draw,
                    sanitized_title,
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
                    text_bbox = draw.textbbox((0, 0), sanitized_title,
                                              font=title_font)
                    title_width = text_bbox[2] - text_bbox[0]
                    draw.text((width // 2 - title_width // 2, 150),
                              sanitized_title, fill="white", font=title_font)
                except:
                    # Ultimate fallback for title
                    draw.text((width // 2, 150), "[Title Error]", fill="white",
                              font=title_font, anchor="mm")

        # Add main text with improved handling of long text
        if sanitized_text:
            # Split text into multiple lines for better layout
            words = sanitized_text.split()
            lines = []
            current_line = []

            for word in words:
                test_line = " ".join(current_line + [word])
                text_bbox = draw.textbbox((0, 0), test_line, font=text_font)
                test_width = text_bbox[2] - text_bbox[0]

                # Check if adding this word exceeds the width
                if test_width < width - 200:
                    current_line.append(word)
                else:
                    lines.append(" ".join(current_line))
                    current_line = [word]

            if current_line:
                lines.append(" ".join(current_line))

            # Calculate start y position to center the text block
            if not lines:
                lines = ["[Text rendering error]"]

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

        # Add navigation arrows and slide counter with better positioning
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

        # Add logo if requested
        if include_logo and logo_path and os.path.exists(logo_path):
            try:
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
            except Exception as e:
                logger.error(f"Error adding logo: {e}")
                # Add error text instead of logo
                draw.text((60, height - 60), "Logo Error", fill=(255, 100, 100),
                          font=navigation_font)

        return image
