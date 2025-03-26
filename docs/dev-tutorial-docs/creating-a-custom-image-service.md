# Tutorial: Creating a Custom Image Service

This tutorial demonstrates how to extend the Instagram Carousel Generator by creating your own custom image service implementation. By the end, you'll have created a unique image service with custom styling and features.

## Overview

The Instagram Carousel Generator uses a flexible, extensible architecture for image generation. The image service follows a class hierarchy:

```
BaseImageService (Abstract Base Class)
├── StandardImageService
└── EnhancedImageService
```

By creating your own implementation, you can:
- Customize the appearance of carousel slides
- Add special effects or branding
- Optimize for specific use cases
- Integrate with other image processing libraries

## Prerequisites

- Basic understanding of Python class inheritance
- Knowledge of Python image processing (PIL/Pillow library)
- Local installation of the Instagram Carousel Generator API

## Step 1: Create the Custom Service Class

First, create a new Python file in the `app/services/image_service` directory. Let's call it `custom_image_service.py`:

```python
"""
Custom image service implementation for Instagram Carousel Generator.

This module provides a custom implementation of the image service with
unique styling and features.
"""
import logging
from typing import Dict, List, Tuple, Any, Optional

from PIL import Image, ImageDraw, ImageFilter, ImageFont

from app.services.image_service.base_image_service import BaseImageService

logger = logging.getLogger(__name__)

class CustomImageService(BaseImageService):
    """
    Custom implementation of the image service with unique styling.

    This implementation adds modern design elements like rounded corners,
    custom gradients, and a different text layout.
    """

    def __init__(self, settings: Dict[str, Any] = None):
        """Initialize with custom default settings."""
        super().__init__(settings)
        # Add custom properties
        self.corner_radius = self.settings.get("corner_radius", 20)
        self.accent_color = self.settings.get("accent_color", (65, 105, 225))  # Royal Blue

    def create_gradient_text(
        self,
        draw: ImageDraw.Draw,
        text: str,
        position: Tuple[int, int],
        font,
        width: int,
        colors: List[Tuple[int, int, int]] = None,
    ) -> Tuple[Image.Image, Tuple[int, int]]:
        """Create gradient text with custom styling."""
        # Apply text sanitization
        text = self.sanitize_text(text)

        if not text:
            # Return empty transparent image if text is empty
            empty_img = Image.new("RGBA", (1, 1), color=(0, 0, 0, 0))
            return empty_img, position

        # Use custom gradient colors if not provided
        if colors is None:
            # Custom gradient: accent color to white
            colors = [self.accent_color, (255, 255, 255)]

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
                color_idx = i / text_width if text_width > 0 else 0
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

            # Add a subtle shadow effect (optional)
            shadow = Image.new("RGBA", text_img.size, color=(0, 0, 0, 0))
            shadow_draw = ImageDraw.Draw(shadow)
            shadow_draw.text((2, 2), text, font=font, fill=(0, 0, 0, 100))
            shadow = shadow.filter(ImageFilter.GaussianBlur(radius=2))

            # Composite the shadow and text
            combined = Image.new("RGBA", text_img.size, color=(0, 0, 0, 0))
            combined.paste(shadow, (0, 0), shadow)
            combined.paste(text_img, (0, 0), text_img)

            return combined, (x, y)

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
        """Create a custom error slide with modern styling."""
        width, height = self.default_width, self.default_height

        # Create base image with a gradient background
        img = Image.new("RGB", (width, height), (40, 40, 40))
        draw = ImageDraw.Draw(img)

        # Add gradient background
        for y in range(height):
            # Create a subtle gradient from dark to slightly lighter
            color_ratio = y / height
            r = int(40 + color_ratio * 20)
            g = int(40 + color_ratio * 20)
            b = int(40 + color_ratio * 30)  # Slight blue tint at bottom
            draw.line([(0, y), (width, y)], fill=(r, g, b))

        # Load fonts
        try:
            title_font = self.safe_load_font(self.default_font_bold, 60)
            text_font = self.safe_load_font(self.default_font, 32)
            small_font = self.safe_load_font(self.default_font, 24)
        except Exception as e:
            logger.warning(f"Could not load custom fonts: {e}")
            title_font = ImageFont.load_default()
            text_font = ImageFont.load_default()
            small_font = ImageFont.load_default()

        # Draw error title with gradient
        error_title = "Error Creating Slide"
        title_gradient, pos = self.create_gradient_text(
            draw, error_title, (width // 2, 150), title_font, width,
            [(255, 100, 100), (255, 200, 200)]  # Red gradient for error
        )
        img.paste(title_gradient, pos, title_gradient)

        # Simplified error message
        simple_error = "Unicode character issue" if "codec can't encode character" in error_message else "Image creation error"
        draw.text(
            (width // 2, height // 2 - 50),
            simple_error,
            fill=self.accent_color,
            font=text_font,
            anchor="mm"
        )

        # Draw the technical error details
        error_details = error_message
        if len(error_details) > 100:
            error_details = error_details[:97] + "..."

        # Wrap text to multiple lines
        wrapped_lines = self._wrap_text(draw, error_details, small_font, width - 200)
        y_pos = height // 2 + 20

        for line in wrapped_lines:
            draw.text(
                (width // 2, y_pos),
                line,
                fill=(200, 200, 200),
                font=small_font,
                anchor="mm"
            )
            y_pos += 30

        # Add a helpful suggestion
        draw.text(
            (width // 2, height // 2 + 150),
            "Please check your input text for special characters",
            fill=(180, 180, 255),
            font=text_font,
            anchor="mm"
        )

        # Add slide counter with accent color
        counter_text = f"{slide_number}/{total_slides}"
        draw.text(
            (width // 2, height - 50),
            counter_text,
            fill=self.accent_color,
            font=small_font,
            anchor="mm"
        )

        # Add decorative elements
        self._add_decorative_elements(draw, width, height)

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
        """Create a custom slide with modern design elements."""
        # Get settings with defaults
        width = self.settings.get("width", self.default_width)
        height = self.settings.get("height", self.default_height)
        bg_color = self.settings.get("bg_color", self.default_bg_color)

        # Create base image
        img = Image.new("RGB", (width, height), bg_color)
        draw = ImageDraw.Draw(img)

        # Add subtle gradient background
        for y in range(height):
            # Create a subtle gradient
            color_ratio = y / height
            r = int(bg_color[0] + color_ratio * 10)
            g = int(bg_color[1] + color_ratio * 10)
            b = int(bg_color[2] + color_ratio * 15)  # Slight blue tint at bottom
            draw.line([(0, y), (width, y)], fill=(r, g, b))

        # Load fonts
        title_font = self.safe_load_font(self.settings.get("title_font", self.default_font_bold), 60)
        text_font = self.safe_load_font(self.settings.get("text_font", self.default_font), 48)
        navigation_font = self.safe_load_font(self.settings.get("nav_font", self.default_font), 36)

        # Sanitize text content
        sanitized_title = self.sanitize_text(title) if title else None
        sanitized_text = self.sanitize_text(text)

        # Add decorative accent line at the top
        line_thickness = 4
        draw.rectangle(
            [(width // 2 - 100, 80), (width // 2 + 100, 80 + line_thickness)],
            fill=self.accent_color
        )

        # Add title with gradient effect (only on first slide)
        if sanitized_title:
            try:
                # Create gradient text from accent color to white
                gradient_text, pos = self.create_gradient_text(
                    draw,
                    sanitized_title,
                    (width // 2, 150),
                    title_font,
                    width,
                    [self.accent_color, (255, 255, 255)],  # Accent to white gradient
                )
                img.paste(gradient_text, pos, gradient_text)
            except Exception as e:
                logger.error(f"Error creating gradient title: {e}")
                # Fallback to plain text title
                draw.text(
                    (width // 2, 150),
                    sanitized_title,
                    fill="white",
                    font=title_font,
                    anchor="mm"
                )

        # Add main text with improved layout
        if sanitized_text:
            # Split text into multiple lines for better layout
            lines = self._wrap_text(draw, sanitized_text, text_font, width - 200)

            # Calculate start y position to center the text block
            line_height = 60
            total_text_height = len(lines) * line_height
            y_position = height / 2 - total_text_height / 2

            # Draw each line of text
            for line in lines:
                try:
                    # Create a subtle gradient effect for each line
                    gradient_line, pos = self.create_gradient_text(
                        draw,
                        line,
                        (width // 2, y_position + line_height // 2),
                        text_font,
                        width,
                        [(220, 220, 240), (255, 255, 255)]  # Subtle gradient for body text
                    )
                    img.paste(gradient_line, pos, gradient_line)
                except Exception as e:
                    logger.error(f"Error rendering text line: {e}")
                    # Fallback using direct drawing
                    draw.text(
                        (width / 2, y_position + line_height // 2),
                        line,
                        fill="white",
                        font=text_font,
                        anchor="mm",
                    )

                y_position += line_height

        # Add custom navigation indicators
        self._add_custom_navigation(draw, slide_number, total_slides, navigation_font, width, height)

        # Add logo if requested
        if include_logo and logo_path:
            self._add_logo_with_style(img, logo_path, width, height)

        # Apply rounded corners effect (if enabled)
        if self.corner_radius > 0:
            img = self._apply_rounded_corners(img, self.corner_radius)

        return img

    def _wrap_text(self, draw, text, font, max_width):
        """Wrap text to fit within the specified width."""
        words = text.split()
        lines = []
        current_line = []

        for word in words:
            test_line = " ".join(current_line + [word])
            text_bbox = draw.textbbox((0, 0), test_line, font=font)
            test_width = text_bbox[2] - text_bbox[0]

            if test_width < max_width:
                current_line.append(word)
            else:
                lines.append(" ".join(current_line))
                current_line = [word]

        if current_line:
            lines.append(" ".join(current_line))

        return lines

    def _add_custom_navigation(self, draw, slide_number, total_slides, font, width, height):
        """Add custom navigation indicators."""
        # Draw slide counter in a stylish way
        counter_text = f"{slide_number}/{total_slides}"

        # Create a small indicator bar at the bottom
        indicator_y = height - 30
        total_width = 200
        item_width = total_width / total_slides

        # Draw background bar
        draw.rectangle(
            [(width/2 - total_width/2, indicator_y - 5),
             (width/2 + total_width/2, indicator_y + 5)],
            fill=(60, 60, 70)
        )

        # Draw current position
        draw.rectangle(
            [(width/2 - total_width/2 + (slide_number-1) * item_width, indicator_y - 5),
             (width/2 - total_width/2 + slide_number * item_width, indicator_y + 5)],
            fill=self.accent_color
        )

        # Draw counter text above the bar
        draw.text(
            (width / 2, indicator_y - 25),
            counter_text,
            fill="white",
            font=font,
            anchor="mm"
        )

        # Add navigation arrows with style
        if slide_number > 1:
            # Left arrow
            draw.text((40, height / 2), "←", fill=self.accent_color, font=font)

        if slide_number < total_slides:
            # Right arrow
            draw.text(
                (width - 40, height / 2),
                "→",
                fill=self.accent_color,
                font=font,
                anchor="ra"
            )

    def _add_decorative_elements(self, draw, width, height):
        """Add decorative elements to slides."""
        # Add some subtle decorative elements in the corners
        corner_size = 40
        line_thickness = 3

        # Top left corner
        draw.rectangle(
            [(20, 20), (20 + corner_size, 20 + line_thickness)],
            fill=self.accent_color
        )
        draw.rectangle(
            [(20, 20), (20 + line_thickness, 20 + corner_size)],
            fill=self.accent_color
        )

        # Bottom right corner
        draw.rectangle(
            [(width - 20 - corner_size, height - 20 - line_thickness),
             (width - 20, height - 20)],
            fill=self.accent_color
        )
        draw.rectangle(
            [(width - 20 - line_thickness, height - 20 - corner_size),
             (width - 20, height - 20)],
            fill=self.accent_color
        )

    def _add_logo_with_style(self, image, logo_path, width, height):
        """Add logo with custom styling."""
        try:
            if os.path.exists(logo_path):
                logo = Image.open(logo_path).convert("RGBA")

                # Resize logo to be 10% of the image width
                logo_size = int(width * 0.12)

                # Use LANCZOS if available, otherwise fallback to ANTIALIAS
                resampling_method = getattr(Image, "LANCZOS", Image.ANTIALIAS)
                logo = logo.resize((logo_size, logo_size), resampling_method)

                # Add a subtle shadow effect to the logo
                shadow = Image.new("RGBA", logo.size, (0, 0, 0, 0))
                shadow_draw = ImageDraw.Draw(shadow)
                shadow_draw.ellipse(
                    [(0, 0), (logo_size, logo_size)],
                    fill=(0, 0, 0, 100)
                )
                shadow = shadow.filter(ImageFilter.GaussianBlur(radius=3))

                # Position logo in bottom left corner with padding
                logo_position = (40, height - logo_size - 40)
                shadow_position = (42, height - logo_size - 38)  # Offset for shadow

                # Paste the shadow first
                image.paste(shadow, shadow_position, shadow)

                # Create a mask for the logo (circle)
                mask = Image.new("L", logo.size, 0)
                mask_draw = ImageDraw.Draw(mask)
                mask_draw.ellipse([(0, 0), (logo_size, logo_size)], fill=255)

                # Paste the logo with circular mask
                image.paste(logo, logo_position, mask)
            else:
                logger.warning(f"Logo file not found: {logo_path}")
        except Exception as e:
            logger.error(f"Error adding logo: {e}")

    def _apply_rounded_corners(self, image, radius):
        """Apply rounded corners to the image."""
        try:
            circle = Image.new('L', (radius * 2, radius * 2), 0)
            draw = ImageDraw.Draw(circle)
            draw.ellipse((0, 0, radius * 2, radius * 2), fill=255)

            alpha = Image.new('L', image.size, 255)

            w, h = image.size
            alpha.paste(circle.crop((0, 0, radius, radius)), (0, 0))
            alpha.paste(circle.crop((radius, 0, radius * 2, radius)), (w - radius, 0))
            alpha.paste(circle.crop((0, radius, radius, radius * 2)), (0, h - radius))
            alpha.paste(circle.crop((radius, radius, radius * 2, radius * 2)), (w - radius, h - radius))

            image.putalpha(alpha)

            # Create a new image with a background color to replace transparency
            bg_color = self.settings.get("bg_color", self.default_bg_color)
            new_img = Image.new("RGB", image.size, bg_color)
            new_img.paste(image, (0, 0), image)

            return new_img
        except Exception as e:
            logger.error(f"Error applying rounded corners: {e}")
            return image
```

## Step 2: Register the Custom Service Type

Next, update the factory module to include your new service type. Open `app/services/image_service/factory.py` and add your custom service:

```python
from enum import Enum
from typing import Any, Dict, Optional

from app.services.image_service.base_image_service import BaseImageService
from app.services.image_service.enhanced_image_service import EnhancedImageService
from app.services.image_service.standard_image_service import StandardImageService
from app.services.image_service.custom_image_service import CustomImageService  # Import your service

class ImageServiceType(Enum):
    """Enum defining available image service implementations."""
    STANDARD = "standard"
    ENHANCED = "enhanced"
    CUSTOM = "custom"  # Add your service type

def get_image_service(
    service_type: str = ImageServiceType.ENHANCED.value,
    settings: Optional[Dict[str, Any]] = None,
) -> BaseImageService:
    """
    Get the appropriate image service implementation.

    Args:
        service_type: The type of image service to retrieve
        settings: Optional dictionary of settings to pass to the image service

    Returns:
        An instance of BaseImageService implementation

    Raises:
        ValueError: If an invalid service_type is provided
    """
    settings = settings or {}

    if service_type == ImageServiceType.STANDARD.value:
        return StandardImageService(settings)
    elif service_type == ImageServiceType.ENHANCED.value:
        return EnhancedImageService(settings)
    elif service_type == ImageServiceType.CUSTOM.value:  # Add your service case
        return CustomImageService(settings)
    else:
        available_types = [t.value for t in ImageServiceType]
        raise ValueError(
            f"Invalid image service type: {service_type}. Available types: "
            f"{', '.join(available_types)}"
        )
```

## Step 3: Update `__init__.py`

Update the `app/services/image_service/__init__.py` file to include your new service:

```python
from .base_image_service import (
    BaseImageService,
    FontLoadError,
    ImageCreationError,
    ImageServiceError,
    TextRenderingError,
)
from .custom_image_service import CustomImageService  # Add this import
from .enhanced_image_service import EnhancedImageService
from .factory import ImageServiceType, get_default_image_service, get_image_service
from .standard_image_service import StandardImageService

# Make sure to include your service in __all__
__all__ = [
    # Classes
    "BaseImageService",
    "StandardImageService",
    "EnhancedImageService",
    "CustomImageService",  # Add this
    # Factory functions
    "get_image_service",
    "get_default_image_service",
    # Enums
    "ImageServiceType",
    # Exceptions
    "ImageServiceError",
    "ImageCreationError",
    "FontLoadError",
    "TextRenderingError",
]
```

## Step 4: Register in the Service Provider

Update the service registration in `app/core/services_setup.py`:

```python
def register_image_services(provider: ServiceProvider):
    """
    Register different image service implementations.

    Args:
        provider: The service provider to register with
    """
    # Get default image service settings
    image_settings = get_image_service_settings()

    # Register Standard Image Service
    provider.register(
        BaseImageService,
        lambda: get_image_service(ImageServiceType.STANDARD.value, image_settings),
        singleton=True,
    )
    provider._services[BaseImageService]["StandardImageService"] = provider._services[
        BaseImageService
    ][BaseImageService.__name__]

    # Register Enhanced Image Service
    provider.register(
        BaseImageService,
        lambda: get_image_service(ImageServiceType.ENHANCED.value, image_settings),
        singleton=True,
    )
    provider._services[BaseImageService]["EnhancedImageService"] = provider._services[
        BaseImageService
    ][BaseImageService.__name__]

    # Register Custom Image Service
    provider.register(
        BaseImageService,
        lambda: get_image_service(ImageServiceType.CUSTOM.value, image_settings),
        singleton=True,
    )
    provider._services[BaseImageService]["CustomImageService"] = provider._services[
        BaseImageService
    ][BaseImageService.__name__]

    logger.info("Image services registered")
```

## Step 5: Create a FastAPI Dependency

Create a dependency to inject your custom service in `app/api/dependencies.py`:

```python
def get_custom_image_service() -> BaseImageService:
    """
    Provide a custom image service instance from the service provider.

    This uses the registered custom image service from the service provider.

    Returns:
        BaseImageService: Custom image service implementation
    """
    return get_service(BaseImageService, key="CustomImageService")
```

## Step 6: Create a Test Endpoint

Create a special endpoint to test your custom service:

```python
@router.post("/generate-custom-carousel", response_model=CarouselResponse, tags=["carousel"])
async def generate_custom_carousel(
    request: CarouselRequest,
    background_tasks: BackgroundTasks,
    http_request: Request,
    image_service: BaseImageService = Depends(get_custom_image_service),
    _: None = Depends(get_heavy_rate_limit),
):
    """
    Generate Instagram carousel images with custom styling.

    This endpoint uses the custom image service implementation with unique styling.

    Args:
        request: Carousel content including title, slides text, and logo preferences
        background_tasks: FastAPI background tasks for scheduling cleanup
        http_request: The FastAPI request object
        image_service: Custom image service implementation
        _: Rate limiting dependency

    Returns:
        JSON response with status, carousel ID, slide images, and processing information
    """
    # Implementation follows the same pattern as the standard generate_carousel endpoint
    # but uses the custom image service
    # ...
```

## Step 7: Test Your Custom Service

Test your custom implementation:

```bash
# Start the API server
uvicorn app.main:create_app --factory --reload

# Send a test request to your custom endpoint
curl -X POST "http://localhost:5001/api/v1/generate-custom-carousel" \
  -H "Content-Type: application/json" \
  -d '{
    "carousel_title": "Custom Styled Carousel",
    "slides": [
      {"text": "This slide uses our custom styling"},
      {"text": "With rounded corners and accent colors"},
      {"text": "Try it out today!"}
    ],
    "include_logo": false
  }'
```

## Step 8: Customize Further

You can continue customizing your implementation by:

1. Adding more configuration options
2. Creating special effects for text or backgrounds
3. Adding new slide layout templates
4. Implementing special formatting for certain types of content

## Key Concepts Learned

Through this tutorial, you've learned how to:

1. **Extend the Base Class**: Create a new implementation by extending `BaseImageService`
2. **Override Methods**: Customize behavior by overriding base class methods
3. **Add New Features**: Implement new features and visual styles
4. **Register New Services**: Integrate your custom service with the dependency injection system
5. **Create API Endpoints**: Expose your custom service through the API

## Advanced Customization Ideas

Here are some ideas for further customization:

1. **Theme Support**: Add various themes (light, dark, colorful) that users can select
2. **Layout Templates**: Create different slide layouts for different content types
3. **Special Effects**: Add text animations, 3D effects, or other visual elements
4. **Metadata Integration**: Add support for including metadata like copyright info, timestamps
5. **Custom Fonts**: Add support for custom font loading from files or URLs

## Conclusion

By creating a custom image service, you've extended the Instagram Carousel Generator with your own unique styling and features. This demonstrates the extensibility of the system's architecture and how it can be adapted to meet specific needs.

The same approach can be used to customize other aspects of the system, such as storage services, text processing, or API behavior.
