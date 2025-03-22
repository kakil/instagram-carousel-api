# Instagram Carousel Generator - Configuration Guide

This document explains the configuration options available for the Instagram Carousel Generator API.

## Configuration Overview

The application uses a centralized configuration system based on Pydantic's `BaseSettings`. This allows for:

- Default values for all settings
- Environment variable overrides
- `.env` file support
- Type validation and conversion

## Configuration Methods (Priority Order)

1. Environment variables (highest priority)
2. `.env` file values
3. Default values (lowest priority)

## Creating Your Configuration

1. Copy the `.env.example` file to `.env`:
   ```bash
   cp .env.example .env
   ```

2. Edit the `.env` file with your specific values:
   ```bash
   nano .env
   ```

## Configuration Categories

### API Settings

| Variable | Description | Default | Required |
|----------|-------------|---------|----------|
| `PROJECT_NAME` | Name of the project | "Instagram Carousel Generator" | No |
| `API_PREFIX` | Prefix for all API endpoints | "/api" | No |
| `API_VERSION` | API version for endpoints | "v1" | No |
| `DEBUG` | Enable debug mode | True | No |
| `API_KEY` | API key for authentication | None | Yes (for production) |

### Server Settings

| Variable | Description | Default | Required |
|----------|-------------|---------|----------|
| `HOST` | Host to bind the server to | "localhost" | No |
| `PORT` | Port to run the server on | 5001 | No |
| `PRODUCTION` | Whether running in production mode | False | No |

### Public Access Settings

| Variable | Description | Default | Required |
|----------|-------------|---------|----------|
| `PUBLIC_BASE_URL` | Base URL for generated image URLs | "http://localhost:5001" | Yes (for production) |

### Path Settings

| Variable | Description | Default | Required |
|----------|-------------|---------|----------|
| `TEMP_DIR` | Path to temporary directory | "{BASE_DIR}/static/temp" | No |
| `STATIC_DIR` | Path to static files directory | "{BASE_DIR}/static" | No |
| `ASSETS_DIR` | Path to assets directory | "{BASE_DIR}/static/assets" | No |
| `PRODUCTION_TEMP_DIR` | Path to temp directory in production | "/var/www/api.kitwanaakil.com/public_html/instagram-carousel-api/static/temp" | No |

### Image Settings

| Variable | Description | Default | Required |
|----------|-------------|---------|----------|
| `DEFAULT_WIDTH` | Default width for images | 1080 | No |
| `DEFAULT_HEIGHT` | Default height for images | 1080 | No |
| `DEFAULT_BG_COLOR_R` | Red component of background color | 18 | No |
| `DEFAULT_BG_COLOR_G` | Green component of background color | 18 | No |
| `DEFAULT_BG_COLOR_B` | Blue component of background color | 18 | No |
| `DEFAULT_FONT` | Default font for text | "Arial.ttf" | No |
| `DEFAULT_FONT_BOLD` | Default bold font for titles | "Arial Bold.ttf" | No |

### Storage Settings

| Variable | Description | Default | Required |
|----------|-------------|---------|----------|
| `TEMP_FILE_LIFETIME_HOURS` | Hours before deleting temporary files | 24 | No |

### Logging Settings

| Variable | Description | Default | Required |
|----------|-------------|---------|----------|
| `LOG_LEVEL` | Logging level | "INFO" | No |

### CORS Settings

| Variable | Description | Default | Required |
|----------|-------------|---------|----------|
| `ALLOW_ORIGINS` | Allowed CORS origins | "*" | No |
| `ALLOW_CREDENTIALS` | Allow credentials in CORS | True | No |
| `ALLOW_METHODS` | Allowed HTTP methods | "*" | No |
| `ALLOW_HEADERS` | Allowed HTTP headers | "*" | No |

### Security Settings

| Variable | Description | Default | Required |
|----------|-------------|---------|----------|
| `RATE_LIMIT_MAX_REQUESTS` | Maximum requests per window | 100 | No |
| `RATE_LIMIT_WINDOW_SECONDS` | Time window for rate limiting in seconds | 60 | No |
| `ENABLE_HTTPS_REDIRECT` | Redirect HTTP to HTTPS in production | False | No |

## Production Configuration Recommendations

1. **Security settings:**
   - Set a strong, unique `API_KEY` (minimum 32 characters recommended)
     ```
     # Generate a secure random API key
     python -c "import secrets; print(secrets.token_urlsafe(32))"
     ```
   - Set specific `ALLOW_ORIGINS` instead of wildcard "*"
   - Set `DEBUG=False`
   - Set `ENABLE_HTTPS_REDIRECT=True`
   - Configure appropriate rate limits based on expected usage

2. **Path settings:**
   - Review and set appropriate paths for your server

3. **URL settings:**
   - Set `PUBLIC_BASE_URL` to your production domain with https
   
## Environment-Specific Configurations

### Development Environment

```dotenv
DEBUG=True
API_KEY=""  # Can be empty in development
PUBLIC_BASE_URL="http://localhost:5001"
PRODUCTION=False
LOG_LEVEL="DEBUG"
ALLOW_ORIGINS="*"
```

### Production Environment

```dotenv
DEBUG=False
API_KEY="your-secure-api-key-here"
PUBLIC_BASE_URL="https://api.yourdomain.com"
PRODUCTION=True
LOG_LEVEL="INFO"
ALLOW_ORIGINS="https://yourdomain.com,https://admin.yourdomain.com"
RATE_LIMIT_MAX_REQUESTS=50
RATE_LIMIT_WINDOW_SECONDS=60
ENABLE_HTTPS_REDIRECT=True
```

## Custom Font Configuration

The application uses the following fonts by default:
- `DEFAULT_FONT` for regular text
- `DEFAULT_FONT_BOLD` for titles

To use custom fonts:

1. Place your font files in the `static/assets` directory
2. Update the configuration:

```dotenv
DEFAULT_FONT="YourFont.ttf"
DEFAULT_FONT_BOLD="YourFont-Bold.ttf"
```

## Security Considerations

### API Key Authentication

API key authentication is used to secure the API endpoints. This requires clients to include the API key in either:
- The `X-API-Key` header
- The `api_key` query parameter

Example curl request:
```bash
curl -H "X-API-Key: your-api-key" http://localhost:5001/api/v1/generate-carousel
```

### Rate Limiting

Rate limiting restricts the number of requests a client can make within a specific time window. This helps prevent abuse and ensures fair usage.

Default settings:
- 100 requests per minute per IP address for general endpoints
- 20 requests per minute per IP address for resource-intensive endpoints

### File Access Validation

File access validation prevents directory traversal attacks when accessing generated carousel images. The validation ensures:
- Carousel IDs consist only of alphanumeric characters, hyphens, and underscores
- Filenames follow a safe pattern and don't contain path traversal sequences

### Security Headers

The API automatically adds security headers to all responses:
- `X-Content-Type-Options: nosniff` - Prevents MIME type sniffing
- `X-XSS-Protection: 1; mode=block` - Enables browser XSS protection
- `Strict-Transport-Security` - Enforces HTTPS usage (production only)

## Troubleshooting Configuration Issues

If you encounter issues with configuration:

1. Check that your `.env` file is in the correct location (root project directory)
2. Verify environment variables are correctly set
3. For path issues, check that all referenced directories exist
4. Review logs for configuration-related errors at startup
5. Ensure production directories have correct permissions
6. Test API key authentication with curl:
   ```bash
   curl -H "X-API-Key: your-api-key" http://your-api-domain/health
   ```