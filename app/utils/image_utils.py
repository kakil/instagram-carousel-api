from PIL import Image, ImageDraw
from typing import Tuple, List
import logging
import unicodedata

logger = logging.getLogger(__name__)


def sanitize_text(text):
    """
    Sanitize text by replacing or removing problematic Unicode characters

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
    }

    for char, replacement in replacements.items():
        text = text.replace(char, replacement)

    # Normalize remaining Unicode (NFKD = compatibility decomposition)
    text = unicodedata.normalize('NFKD', text)

    # Remove any remaining non-ASCII characters
    text = ''.join(c for c in text if ord(c) < 128)

    return text


def create_gradient_text(
        draw: ImageDraw.Draw,
        text: str,
        position: Tuple[int, int],
        font,
        width: int,
        colors: List[Tuple[int, int, int]] = None
) -> Tuple[Image.Image, Tuple[int, int]]:
    """
    Create gradient text from one color to another

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
    # Sanitize the text to handle Unicode characters
    text = sanitize_text(text)

    if colors is None:
        # Default black to white gradient
        colors = [(0, 0, 0), (255, 255, 255)]

    try:
        # Get text size
        text_bbox = draw.textbbox((0, 0), text, font=font)
        text_width = text_bbox[2] - text_bbox[0]
        text_height = text_bbox[3] - text_bbox[1]

        # Create a gradient mask
        gradient = Image.new("L", (text_width, text_height), color=0)
        gradient_draw = ImageDraw.Draw(gradient)

        # Create gradient by drawing lines with increasing brightness
        for i in range(text_width):
            color_idx = i / text_width
            r = int(colors[0][0] + color_idx * (colors[1][0] - colors[0][0]))
            g = int(colors[0][1] + color_idx * (colors[1][1] - colors[0][1]))
            b = int(colors[0][2] + color_idx * (colors[1][2] - colors[0][2]))
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
        logger.error(f"Error in create_gradient_text: {str(e)}")
        # Create a simple fallback text image
        fallback_img = Image.new("RGBA", (width, 100), color=(0, 0, 0, 0))
        fallback_draw = ImageDraw.Draw(fallback_img)
        fallback_draw.text((width // 2, 50), text, font=font, fill="white",
                           anchor="mm")
        return fallback_img, (0, position[1] - 50)