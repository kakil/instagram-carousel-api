"""
Standard implementation of the image service module.

This module provides a reliable and straightforward implementation of the image service
for creating Instagram carousel slides. It focuses on core functionality with good error handling.
"""
import logging
import os
from typing import List, Tuple

from PIL import Image, ImageDraw, ImageFont

from app.services.image_service.base_image_service import BaseImageService

logger = logging.getLogger(__name__)


class StandardImageService(BaseImageService):
    """
    Standard implementation of the image service with basic functionality.

    This class provides a simpler implementation that prioritizes reliability
    over advanced features.
    """

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
        # Apply text sanitization
        text = self.sanitize_text(text)

        if not text:
            # Return empty transparent image if text is empty
            empty_img = Image.new("RGBA", (1, 1), color=(0, 0, 0, 0))
            return empty_img, position

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

        except Exception as e:
            logger.error(f"Error in create_gradient_text: {e}")

            # Create a simple fallback text image
            fallback_img = Image.new("RGBA", (width, 100), color=(0, 0, 0, 0))
            fallback_draw = ImageDraw.Draw(fallback_img)
            fallback_draw.text((width // 2, 50), text, font=font, fill="white", anchor="mm")

            return fallback_img, (0, position[1] - 50)

    def create_error_slide(
        self, slide_number: int, total_slides: int, error_message: str
    ) -> Image.Image:
        """
        Create a basic error slide when there's a problem generating a slide.

        Args:
            slide_number: Current slide number
            total_slides: Total number of slides
            error_message: Error message to display

        Returns:
            PIL Image object
        """
        width, height = self.default_width, self.default_height
        img = Image.new("RGB", (width, height), (40, 40, 40))  # Dark gray background
        draw = ImageDraw.Draw(img)

        try:
            # Attempt to load font or fall back to default
            font = self.safe_load_font(self.default_font, 32)
            small_font = self.safe_load_font(self.default_font, 24)
        except Exception:
            font = ImageFont.load_default()
            small_font = ImageFont.load_default()

        # Draw error message
        text_position = (width // 2, height // 2 - 50)
        draw.text(
            text_position,
            "Error creating slide",
            fill=(255, 100, 100),
            anchor="mm",
            font=font,
        )

        # Draw a simplified error message
        simple_error = (
            "Unicode character issue"
            if "codec can't encode character" in error_message
            else "Image creation error"
        )
        text_position = (width // 2, height // 2)
        draw.text(
            text_position,
            simple_error,
            fill=(200, 200, 200),
            anchor="mm",
            font=small_font,
        )

        # Add slide counter
        counter_text = f"{slide_number}/{total_slides}"
        counter_position = (width // 2, height - 50)
        draw.text(counter_position, counter_text, fill="white", anchor="mm", font=small_font)

        return img

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
        width, height = self.default_width, self.default_height
        image = Image.new("RGB", (width, height), self.default_bg_color)
        draw = ImageDraw.Draw(image)

        # Load fonts
        try:
            title_font = self.safe_load_font(self.default_font_bold, 60)
            text_font = self.safe_load_font(self.default_font, 48)
            navigation_font = self.safe_load_font(self.default_font, 36)
        except Exception:
            logger.warning("Custom fonts not found, using default font")
            # Fallback to default font if custom font not available
            title_font = ImageFont.load_default()
            text_font = ImageFont.load_default()
            navigation_font = ImageFont.load_default()

        # Sanitize text content
        sanitized_title = self.sanitize_text(title) if title else None
        sanitized_text = self.sanitize_text(text)

        # Add title with gradient effect (only on first slide)
        if sanitized_title:
            try:
                # Create gradient text from black to white
                gradient_text, pos = self.create_gradient_text(
                    draw,
                    sanitized_title,
                    (width // 2, 150),
                    title_font,
                    width,
                    [(0, 0, 0), (255, 255, 255)],  # Black to white gradient
                )
                image.paste(gradient_text, pos, gradient_text)
            except Exception as e:
                logger.error(f"Error creating gradient title: {e}")
                # Fallback to plain text title
                text_bbox = draw.textbbox((0, 0), sanitized_title, font=title_font)
                title_width = text_bbox[2] - text_bbox[0]
                draw.text(
                    (width // 2 - title_width // 2, 150),
                    sanitized_title,
                    fill="white",
                    font=title_font,
                )

        # Add main text
        # Split text into multiple lines if needed
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
            draw.text(
                (width - 40 - text_width, height / 2),
                "→",
                fill="white",
                font=navigation_font,
            )

        # Add slide counter
        counter_text = f"{slide_number}/{total_slides}"
        text_bbox = draw.textbbox((0, 0), counter_text, font=navigation_font)
        text_width = text_bbox[2] - text_bbox[0]
        text_height = text_bbox[3] - text_bbox[1]
        draw.text(
            (width / 2 - text_width / 2, height - 60 - text_height),
            counter_text,
            fill="white",
            font=navigation_font,
        )

        # Add logo if requested
        if include_logo and logo_path and os.path.exists(logo_path):
            try:
                logo = Image.open(logo_path).convert("RGBA")
                # Resize logo to be 10% of the image width
                logo_size = int(width * 0.1)
                logo = logo.resize(
                    (logo_size, logo_size),
                    Image.LANCZOS if hasattr(Image, "LANCZOS") else Image.ANTIALIAS,
                )

                # Position logo in bottom left corner with padding
                logo_position = (30, height - logo_size - 30)

                # Create a mask for the logo
                mask = logo.split()[3] if len(logo.split()) == 4 else None

                # Paste the logo onto the image
                image.paste(logo, logo_position, mask)
            except Exception as e:
                logger.error(f"Error adding logo: {e}")

        return image
