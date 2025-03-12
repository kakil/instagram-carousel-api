from PIL import Image, ImageDraw, ImageFont
import os
import tempfile
from app.utils.image_utils import create_gradient_text
from app.core.config import settings
from app.models.carousel import SlideContent, SlideResponse
from typing import List, Dict, Any
import logging

logger = logging.getLogger(__name__)


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
            slide_text = slide.text
            slide_number = index + 1
            total_slides = len(slides_data)

            # Create image
            img = create_slide_image(
                carousel_title if index == 0 else None,
                # Only show title on first slide
                slide_text,
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
                "content": file_content.hex()  # Convert binary to hex for JSON
            })

        return image_files


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