# Instagram Carousel Generator

A FastAPI-based application for generating Instagram carousel images with consistent styling.

## Features

- Generate carousel images with consistent dark-themed styling
- Customize title and content text
- Support for multiple slides
- Optional logo inclusion
- Gradient text effects for titles
- API for integration with automation workflows
- Image preview functionality

## Package Structure

```
instagram_carousel_generator/
├── api/                # API endpoints and routing
├── core/               # Core configuration
├── models/             # Data models and schemas
├── services/           # Business logic
│   └── image_service/  # Image generation services
├── utils/              # Utility functions
└── static/             # Static assets and temporary files
```

## Installation

### From Source

```bash
git clone https://github.com/yourusername/instagram-carousel-generator.git
cd instagram-carousel-generator
pip install -e .
```

For development:

```bash
pip install -e ".[dev]"
```

## Quick Start

### Running the API Server

```bash
# Set up environment variables
cp .env.example .env
# Edit .env with your settings

# Run the server
carousel-api
```

Or directly with Python:

```bash
python -m instagram_carousel_generator.main
```

### Using the API

Generate a carousel:

```python
import requests
import json

api_url = "http://localhost:5001/api/v1/generate-carousel"

payload = {
    "carousel_title": "5 Productivity Tips",
    "slides": [
        {"text": "Wake up early and plan your day"},
        {"text": "Use the Pomodoro technique for focus"},
        {"text": "Take regular breaks to recharge"}
    ],
    "include_logo": True,
    "logo_path": "path/to/logo.png"
}

response = requests.post(
    api_url, 
    headers={"Content-Type": "application/json"},
    data=json.dumps(payload)
)

data = response.json()
print(data)
```

## Development

### Architecture

The project follows a modular service-oriented architecture:

1. **API Layer** - Handles HTTP requests and response formatting
2. **Services Layer** - Contains business logic for image generation and storage
3. **Models Layer** - Defines data schemas for request/response validation
4. **Utils Layer** - Provides common utility functions

The image service follows factory pattern with base and specialized implementations:
- `BaseImageService` - Abstract base class defining the interface
- `StandardImageService` - Standard implementation for basic needs
- `EnhancedImageService` - Extended implementation with better error handling

### Testing

```bash
pytest
```

### Code Formatting

```bash
black instagram_carousel_generator
isort instagram_carousel_generator
flake8 instagram_carousel_generator
```

## License

MIT