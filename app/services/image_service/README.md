# Image Service Module

## Overview

The Image Service Module is a core component of the Instagram Carousel Generator that handles the creation of carousel slide images. This module has been refactored to use a class-based architecture with proper inheritance, making it more maintainable, extensible, and easier to test.

## Architecture

The module follows a simple hierarchy:

```
BaseImageService (Abstract Base Class)
├── StandardImageService
└── EnhancedImageService
```

- **BaseImageService**: Defines the interface and common utility methods
- **StandardImageService**: Basic implementation with core functionality
- **EnhancedImageService**: Advanced implementation with improved error handling and text rendering

## Key Features

- **Factory Pattern**: Use `get_image_service()` to create the appropriate service instance
- **Backward Compatibility**: Legacy functions are maintained for smooth migration
- **Improved Error Handling**: More robust handling of text rendering issues
- **Enhanced Unicode Support**: Better handling of special characters and non-ASCII text
- **Clean Inheritance Hierarchy**: Makes it easy to add new service implementations

## Usage

### Basic Usage

```python
from app.services.image_service import get_image_service, ImageServiceType

# Create an enhanced image service
service = get_image_service(ImageServiceType.ENHANCED.value, {
    'width': 1080,
    'height': 1080,
    'bg_color': (18, 18, 18)
})

# Generate carousel images
images = service.create_carousel_images(
    carousel_title="My Carousel",
    slides_data=[{"text": "Slide 1"}, {"text": "Slide 2"}],
    carousel_id="abc123",
    include_logo=True,
    logo_path="/path/to/logo.png"
)
```

### Using with FastAPI Dependency Injection

```python
from fastapi import Depends
from app.services.image_service import get_image_service, ImageServiceType

def get_enhanced_image_service():
    return get_image_service(ImageServiceType.ENHANCED.value, settings)

@router.post("/generate-carousel")
async def generate_carousel(
    request: CarouselRequest,
    image_service = Depends(get_enhanced_image_service)
):
    result = image_service.create_carousel_images(
        request.carousel_title,
        [{"text": slide.text} for slide in request.slides],
        carousel_id,
        request.include_logo,
        request.logo_path
    )
    
    return {"status": "success", "carousel_id": carousel_id, "slides": result}
```

### Legacy Support

For backward compatibility, you can still use the module's functions directly:

```python
from app.services.image_service import create_carousel_images, create_slide_image

# These functions use the default EnhancedImageService under the hood
images = create_carousel_images(
    carousel_title="My Carousel",
    slides_data=[{"text": "Slide 1"}, {"text": "Slide 2"}],
    carousel_id="abc123"
)
```

## Configuration Options

The image service accepts the following settings:

| Setting | Description | Default Value |
|---------|-------------|---------------|
| width | Width of carousel slides in pixels | 1080 |
| height | Height of carousel slides in pixels | 1080 |
| bg_color | Background color as RGB tuple | (18, 18, 18) |
| title_font | Path or name of font for titles | 'Arial Bold.ttf' |
| text_font | Path or name of font for slide text | 'Arial.ttf' |
| nav_font | Path or name of font for navigation | 'Arial.ttf' |
| text_color | Text color as RGB tuple | (255, 255, 255) |
| ascii_only | Whether to only allow ASCII characters | False |
| assets_dir | Directory for assets like fonts and logos | 'static/assets' |

## Extending the Module

### Creating a New Service Implementation

To add a new image service implementation:

1. Create a new class that inherits from `BaseImageService`
2. Implement all required abstract methods
3. Add your new service type to the `ImageServiceType` enum
4. Update the factory function to support your new implementation

Example:

```python
# Add to enum
class ImageServiceType(Enum):
    STANDARD = "standard"
    ENHANCED = "enhanced"
    CUSTOM = "custom"  # Add your new type

# Create your implementation
class CustomImageService(BaseImageService):
    # Implement required methods
    def create_slide_image(self, ...):
        # Custom implementation
    
    def create_gradient_text(self, ...):
        # Custom implementation
    
    def create_error_slide(self, ...):
        # Custom implementation

# Update factory
def get_image_service(service_type, settings=None):
    # ...existing code...
    elif service_type == ImageServiceType.CUSTOM.value:
        return CustomImageService(settings)
    # ...
```

## Testing

To test the image service implementations:

```python
import pytest
from app.services.image_service import get_image_service, ImageServiceType

@pytest.fixture
def standard_service():
    return get_image_service(ImageServiceType.STANDARD.value, {'width': 500, 'height': 500})

@pytest.fixture
def enhanced_service():
    return get_image_service(ImageServiceType.ENHANCED.value, {'width': 500, 'height': 500})

def test_gradient_text(standard_service):
    # Test gradient text creation
    
def test_error_slide(enhanced_service):
    # Test error slide creation
```

## Migration Guide

### Step 1: Update Imports

Replace:
```python
from app.services.improved_image_service import create_carousel_images
```

With:
```python
from app.services.image_service import create_carousel_images
```

### Step 2: Switch to Object-Oriented Approach (Optional)

If you want to take advantage of the new class-based approach:

```python
from app.services.image_service import get_image_service, ImageServiceType

service = get_image_service(ImageServiceType.ENHANCED.value, {
    'width': 1080,
    'height': 1080
})

images = service.create_carousel_images(
    carousel_title="My Carousel",
    slides_data=[{"text": "Slide 1"}, {"text": "Slide 2"}],
    carousel_id="abc123"
)
```

### Step 3: Add FastAPI Dependency for Testing (Optional)

For easier testing and mocking, use FastAPI's dependency injection:

```python
# Define a dependency
def get_image_service_dependency():
    service_settings = {
        'width': settings.DEFAULT_WIDTH,
        'height': settings.DEFAULT_HEIGHT,
        'bg_color': settings.DEFAULT_BG_COLOR
    }
    return get_image_service(ImageServiceType.ENHANCED.value, service_settings)

# Use in endpoint
@router.post("/generate-carousel")
async def generate_carousel(
    request: CarouselRequest,
    image_service = Depends(get_image_service_dependency)
):
    # Use image_service
```