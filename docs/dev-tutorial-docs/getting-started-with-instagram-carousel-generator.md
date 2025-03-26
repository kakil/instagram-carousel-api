# Getting Started with Instagram Carousel Generator

This guide will walk you through the process of setting up and running the Instagram Carousel Generator API on your local machine, configuring it for development or production use, and making your first API request.

## Prerequisites

Before you begin, ensure you have the following installed:

- Python 3.10 or higher
- pip (Python package manager)
- Git (optional, for cloning the repository)
- Docker and Docker Compose (optional, for containerized deployment)

## Installation Options

### Option 1: Direct Installation

1. **Clone or download the repository**

   ```bash
   git clone https://github.com/kakil/instagram-carousel-api.git
   cd instagram-carousel-api
   ```

2. **Create and activate a virtual environment**

   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install the package and dependencies**

   ```bash
   # For regular use
   pip install -e .

   # For development (includes testing dependencies)
   pip install -e ".[dev]"
   ```

4. **Create a configuration file**

   Copy the example environment file and customize it:

   ```bash
   cp .env.example .env
   ```

   Edit the `.env` file with your preferred settings (see Configuration section below).

### Option 2: Docker Installation (Recommended)

1. **Clone or download the repository**

   ```bash
   git clone https://github.com/kakil/instagram-carousel-api.git
   cd instagram-carousel-api
   ```

2. **Set up the Docker environment**

   ```bash
   # Make the setup script executable
   chmod +x scripts/setup-docker-env.sh

   # Run the setup script
   ./scripts/setup-docker-env.sh
   ```

3. **Start the development environment**

   ```bash
   # Start the development environment with hot-reloading
   ./scripts/docker.sh dev
   ```

## Configuration

The Instagram Carousel Generator uses environment variables for configuration. Here are the key settings you can customize:

### API Settings

| Variable | Description | Default |
|----------|-------------|---------|
| `API_PREFIX` | URL prefix for API endpoints | `/api` |
| `API_VERSION` | API version | `v1` |
| `DEBUG` | Enable debug mode | `True` |
| `API_KEY` | API key for authentication | None |

### Server Settings

| Variable | Description | Default |
|----------|-------------|---------|
| `HOST` | Server host | `0.0.0.0` |
| `PORT` | Server port | `5001` |
| `PRODUCTION` | Production mode flag | `False` |
| `PUBLIC_BASE_URL` | Base URL for public access | `http://localhost` |

### Image Settings

| Variable | Description | Default |
|----------|-------------|---------|
| `DEFAULT_WIDTH` | Default carousel image width | `1080` |
| `DEFAULT_HEIGHT` | Default carousel image height | `1080` |
| `DEFAULT_BG_COLOR_R/G/B` | Background color RGB values | `18,18,18` |
| `DEFAULT_FONT` | Default font for text | `Arial.ttf` |
| `DEFAULT_FONT_BOLD` | Default font for titles | `Arial Bold.ttf` |

### Security Settings

| Variable | Description | Default |
|----------|-------------|---------|
| `ALLOW_ORIGINS` | CORS allowed origins | `*` |
| `RATE_LIMIT_MAX_REQUESTS` | Rate limit max requests | `100` |
| `RATE_LIMIT_WINDOW_SECONDS` | Rate limit window seconds | `60` |

For a complete list of configuration options, see the `config.py` file.

## Quick Start

### Running the API

After installation and configuration, start the API server:

#### Using Python directly:

```bash
# Activate virtual environment if not already activated
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Start the server
uvicorn app.main:create_app --factory --host 0.0.0.0 --port 5001 --reload
```

#### Using Docker:

```bash
./scripts/docker.sh dev
```

### Making Your First API Request

Once the API is running, you can make your first request to generate a carousel:

```bash
curl -X POST "http://localhost:5001/api/v1/generate-carousel" \
  -H "Content-Type: application/json" \
  -d '{
    "carousel_title": "My First Carousel",
    "slides": [
      {"text": "This is my first slide with Instagram Carousel Generator"},
      {"text": "It works great for creating consistent branded content"},
      {"text": "Try it out today!"}
    ],
    "include_logo": false
  }'
```

This will return a response with the generated carousel images in binary format (hex-encoded).

To get public URLs for the generated images:

```bash
curl -X POST "http://localhost:5001/api/v1/generate-carousel-with-urls" \
  -H "Content-Type: application/json" \
  -d '{
    "carousel_title": "My First Carousel",
    "slides": [
      {"text": "This is my first slide with Instagram Carousel Generator"},
      {"text": "It works great for creating consistent branded content"},
      {"text": "Try it out today!"}
    ],
    "include_logo": false
  }'
```

### Accessing Documentation

The API comes with built-in documentation powered by Swagger UI and ReDoc:

- Swagger UI: http://localhost:5001/docs
- ReDoc: http://localhost:5001/redoc

## Next Steps

Now that you have the API up and running, you can:

1. Explore the [Core Concepts Guide](core-concepts.md) to understand how the system works
2. Follow the [Basic Usage Tutorial](tutorials/basic-usage.md) for more examples
3. Learn about [Customizing Carousel Styling](tutorials/customizing-styling.md)
4. Check out the [API Reference](api-reference.md) for detailed endpoint information

## Troubleshooting

### Common Issues

1. **Port already in use**

   If port 5001 is already in use, you can change the port in the `.env` file or use the command-line argument:

   ```bash
   uvicorn app.main:create_app --factory --host 0.0.0.0 --port 5002 --reload
   ```

2. **Font loading errors**

   The API requires certain fonts to render text properly. If you see font-related errors:

   - Ensure Arial.ttf and Arial Bold.ttf are installed on your system, or
   - Place them in the `static/assets` directory, or
   - Configure different fonts in the `.env` file

3. **Temporary directory permissions**

   If you see errors related to temporary file creation:

   ```
   Check that the TEMP_DIR setting points to a writable directory
   Ensure the process has write permissions for that directory
   ```

For more troubleshooting help, check out the [Troubleshooting Guide](troubleshooting.md).
