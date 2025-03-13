from PIL import Image, ImageDraw, ImageFont
import os
import tempfile
from app.utils.image_utils import create_gradient_text
from app.core.config import settings
from app.models.carousel import SlideContent, SlideResponse
from typing import List, Dict, Any
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


def create_carousel_images(
        carousel_title: str,
        slides_data: List[SlideContent],
        carousel_id: str,
        include_logo: bool = False,
        logo_path: str = None
) -> List[Dict[str, Any]]:
    """
    Create carousel images for Instagram based on text content

    Args:
        carousel_title: The title for the carousel
        slides_data: List of SlideContent objects with slide text
        carousel_id: Unique identifier for the carousel
        include_logo: Whether to include a logo
        logo_path: Path to the logo file

    Returns:
        List of dictionaries with image data
    """
    # Create a temporary directory for the images
    with tempfile.TemporaryDirectory() as temp_dir:
        image_files = []

        # Generate each slide
        for index, slide in enumerate(slides_data):
            try:
                # Get slide text and sanitize
                slide_text = slide.text
                sanitized_title = sanitize_text(
                    carousel_title) if carousel_title else None
                sanitized_text = sanitize_text(slide_text)

                slide_number = index + 1
                total_slides = len(slides_data)

                # Create image
                img = create_slide_image(
                    sanitized_title if index == 0 else None,
                    # Only show title on first slide
                    sanitized_text,
                    slide_number,
                    total_slides,
                    include_logo,
                    logo_path
                )

                # Save image
                filename = os.path.join(temp_dir, f"slide_{slide_number}.png")
                img.save(filename)

                # Read file and convert to hex
                with open(filename, "rb") as f:
                    file_content = f.read()

                # Add to result
                image_files.append({
                    "filename": f"slide_{slide_number}.png",
                    "content": file_content.hex()
                    # Convert binary to hex for JSON
                })
            except Exception as e:
                logger.error(f"Error processing slide {index + 1}: {str(e)}")
                # Create a basic error slide
                error_img = create_error_slide(index + 1, len(slides_data),
                                               str(e))
                filename = os.path.join(temp_dir,
                                        f"slide_{index + 1}_error.png")
                error_img.save(filename)

                with open(filename, "rb") as f:
                    file_content = f.read()

                image_files.append({
                    "filename": f"slide_{index + 1}_error.png",
                    "content": file_content.hex()
                })

        return image_files


def create_error_slide(slide_number, total_slides, error_message):
    """Create a basic error slide when there's a problem generating a slide"""
    width, height = settings.DEFAULT_WIDTH, settings.DEFAULT_HEIGHT
    img = Image.new("RGB", (width, height),
                    (40, 40, 40))  # Dark gray background
    draw = ImageDraw.Draw(img)

    try:
        # Attempt to load font or fall back to default
        font = ImageFont.truetype(settings.DEFAULT_FONT, 32)
        small_font = ImageFont.truetype(settings.DEFAULT_FONT, 24)
    except Exception:
        font = ImageFont.load_default()
        small_font = ImageFont.load_default()

    # Draw error message
    text_position = (width // 2, height // 2 - 50)
    draw.text(text_position, "Error creating slide", fill=(255, 100, 100),
              anchor="mm", font=font)

    # Draw a simplified error message
    simple_error = "Unicode character issue" if "codec can't encode character" in error_message else "Image creation error"
    text_position = (width // 2, height // 2)
    draw.text(text_position, simple_error, fill=(200, 200, 200), anchor="mm",
              font=small_font)

    # Add slide counter
    counter_text = f"{slide_number}/{total_slides}"
    counter_position = (width // 2, height - 50)
    draw.text(counter_position, counter_text, fill="white", anchor="mm",
              font=small_font)

    return img


def create_slide_image(
        title: str,
        text: str,
        slide_number: int,
        total_slides: int,
        include_logo: bool = False,
        logo_path: str = None
) -> Image.Image:
    """Create an Instagram carousel slide with the specified styling"""
    width, height = settings.DEFAULT_WIDTH, settings.DEFAULT_HEIGHT
    image = Image.new("RGB", (width, height), settings.DEFAULT_BG_COLOR)
    draw = ImageDraw.Draw(image)

    # Load fonts
    try:
        title_font = ImageFont.truetype(settings.DEFAULT_FONT_BOLD, 60)
        text_font = ImageFont.truetype(settings.DEFAULT_FONT, 48)
        navigation_font = ImageFont.truetype(settings.DEFAULT_FONT, 36)
    except IOError:
        logger.warning("Custom fonts not found, using default font")
        # Fallback to default font if custom font not available
        title_font = ImageFont.load_default()
        text_font = ImageFont.load_default()
        navigation_font = ImageFont.load_default()

    # Add title with gradient effect (only on first slide)
    if title:
        try:
            # Create gradient text from black to white
            gradient_text, pos = create_gradient_text(
                draw,
                title,
                (width // 2, 150),
                title_font,
                width,
                [(0, 0, 0), (255, 255, 255)]  # Black to white gradient
            )
            image.paste(gradient_text, pos, gradient_text)
        except Exception as e:
            logger.error(f"Error creating gradient title: {str(e)}")
            # Fallback to plain text title
            text_bbox = draw.textbbox((0, 0), title, font=title_font)
            title_width = text_bbox[2] - text_bbox[0]
            draw.text((width // 2 - title_width // 2, 150), title, fill="white",
                      font=title_font)

    # Add main text
    # Split text into multiple lines if needed
    words = text.split()
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
    total_text_height = len(lines) * 60  # Line height
    y_position = height / 2 - total_text_height / 2

    # Draw each line of text
    for line in lines:
        text_bbox = draw.textbbox((0, 0), line, font=text_font)
        text_width = text_bbox[2] - text_bbox[0]
        text_height = text_bbox[3] - text_bbox[1]
        x_position = width / 2 - text_width / 2

        draw.text((x_position, y_position), line, fill="white", font=text_font)
        y_position += 60

    # Add navigation arrows and slide counter
    if slide_number > 1:
        draw.text((40, height / 2), "←", fill="white", font=navigation_font)

    if slide_number < total_slides:
        text_bbox = draw.textbbox((0, 0), "→", font=navigation_font)
        text_width = text_bbox[2] - text_bbox[0]
        draw.text((width - 40 - text_width, height / 2), "→", fill="white",
                  font=navigation_font)

    # Add slide counter
    counter_text = f"{slide_number}/{total_slides}"
    text_bbox = draw.textbbox((0, 0), counter_text, font=navigation_font)
    text_width = text_bbox[2] - text_bbox[0]
    text_height = text_bbox[3] - text_bbox[1]
    draw.text((width / 2 - text_width / 2, height - 60 - text_height),
              counter_text, fill="white", font=navigation_font)

    # Add logo if requested
    if include_logo and logo_path and os.path.exists(logo_path):
        try:
            logo = Image.open(logo_path).convert("RGBA")
            # Resize logo to be 10% of the image width
            logo_size = int(width * 0.1)
            logo = logo.resize((logo_size, logo_size), Image.LANCZOS)

            # Position logo in bottom left corner with padding
            logo_position = (30, height - logo_size - 30)

            # Create a mask for the logo
            mask = logo.split()[3] if len(logo.split()) == 4 else None

            # Paste the logo onto the image
            image.paste(logo, logo_position, mask)
        except Exception as e:
            logger.error(f"Error adding logo: {str(e)}")

    return image