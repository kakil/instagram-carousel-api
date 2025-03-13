from PIL import Image, ImageDraw
from typing import Tuple, List


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
    if colors is None:
        # Default black to white gradient
        colors = [(0, 0, 0), (255, 255, 255)]

    # Ensure text is a string and handle potential encoding issues
    if not isinstance(text, str):
        text = str(text)

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
    text_img = Image.new("RGBA", (text_width, text_height), color=(0, 0, 0, 0))
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