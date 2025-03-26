# API Reference Documentation

This document provides detailed information about all available endpoints in the Instagram Carousel Generator API.

## Base URL

```
http://localhost:5001/api/v1
```

For production deployments, replace the base URL with your domain:

```
https://your-domain.com/api/v1
```

## Authentication

Most endpoints require authentication using an API key. Include your API key in requests using one of these methods:

**Header-based authentication (recommended):**
```
X-API-Key: your_api_key_here
```

**Query parameter authentication:**
```
?api_key=your_api_key_here
```

## Endpoints

### Carousel Generation

#### Generate Carousel

Generates carousel images and returns the binary data.

```
POST /generate-carousel
```

**Request Body:**

```json
{
  "carousel_title": "My First Carousel",
  "slides": [
    {"text": "Slide 1 content"},
    {"text": "Slide 2 content"},
    {"text": "Slide 3 content"}
  ],
  "include_logo": false,
  "logo_path": null,
  "settings": {
    "width": 1080,
    "height": 1080,
    "bg_color": [18, 18, 18]
  }
}
```

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `carousel_title` | string | Yes | Title for the carousel |
| `slides` | array | Yes | Array of slide objects, each with a `text` field |
| `include_logo` | boolean | No | Whether to include a logo (default: false) |
| `logo_path` | string | No | Path to the logo file (relative to server) |
| `settings` | object | No | Optional settings to override defaults |

**Response:**

```json
{
  "status": "success",
  "carousel_id": "a1b2c3d4",
  "slides": [
    {
      "filename": "slide_1.png",
      "content": "89504e470d0a1a0a..."  // Hex-encoded PNG data
    },
    {
      "filename": "slide_2.png",
      "content": "89504e470d0a1a0a..."
    },
    {
      "filename": "slide_3.png",
      "content": "89504e470d0a1a0a..."
    }
  ],
  "processing_time": 1.25,
  "warnings": []
}
```

| Field | Type | Description |
|-------|------|-------------|
| `status` | string | Status of the operation (success or error) |
| `carousel_id` | string | Unique identifier for the carousel |
| `slides` | array | Array of slide objects with filename and content |
| `processing_time` | number | Time taken to generate the carousel in seconds |
| `warnings` | array | Any warnings that occurred during generation |

**Status Codes:**

| Code | Description |
|------|-------------|
| 200 | Success |
| 401 | Unauthorized - Invalid or missing API key |
| 422 | Validation error - Invalid request data |
| 429 | Too Many Requests - Rate limit exceeded |
| 500 | Server error |

**Example Request:**

```bash
curl -X POST "http://localhost:5001/api/v1/generate-carousel" \
  -H "Content-Type: application/json" \
  -H "X-API-Key: your_api_key_here" \
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

#### Generate Carousel with URLs

Generates carousel images and returns URLs for accessing them.

```
POST /generate-carousel-with-urls
```

**Request Body:**
Same as `/generate-carousel`

**Response:**

```json
{
  "status": "success",
  "carousel_id": "a1b2c3d4",
  "slides": [
    {
      "filename": "slide_1.png",
      "content": "89504e470d0a1a0a..."  // Hex-encoded PNG data
    },
    {
      "filename": "slide_2.png",
      "content": "89504e470d0a1a0a..."
    },
    {
      "filename": "slide_3.png",
      "content": "89504e470d0a1a0a..."
    }
  ],
  "public_urls": [
    "http://localhost:5001/api/v1/temp/a1b2c3d4/slide_1.png",
    "http://localhost:5001/api/v1/temp/a1b2c3d4/slide_2.png",
    "http://localhost:5001/api/v1/temp/a1b2c3d4/slide_3.png"
  ],
  "processing_time": 1.25,
  "warnings": []
}
```

Additional fields compared to `/generate-carousel`:

| Field | Type | Description |
|-------|------|-------------|
| `public_urls` | array | Array of URLs for accessing the generated images |

**Status Codes:**
Same as `/generate-carousel`

**Example Request:**

```bash
curl -X POST "http://localhost:5001/api/v1/generate-carousel-with-urls" \
  -H "Content-Type: application/json" \
  -H "X-API-Key: your_api_key_here" \
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

### File Access

#### Get Temporary File

Retrieves a generated image file by its carousel ID and filename.

```
GET /temp/{carousel_id}/{filename}
```

**Path Parameters:**

| Parameter | Type | Description |
|-----------|------|-------------|
| `carousel_id` | string | The unique carousel identifier |
| `filename` | string | The filename of the image |

**Response:**
The image file with appropriate content type header.

**Status Codes:**

| Code | Description |
|------|-------------|
| 200 | Success |
| 403 | Forbidden - Invalid file access attempt |
| 404 | Not Found - File not found |
| 500 | Server error |

**Example Request:**

```bash
curl -X GET "http://localhost:5001/api/v1/temp/a1b2c3d4/slide_1.png" -o slide_1.png
```

### Monitoring and Management

#### Debug Temporary Directory

Debug endpoint to view the contents of the temporary directory.

```
GET /debug-temp
```

**Authentication:**
Requires an API key.

**Response:**

```json
{
  "temp_dir": "/app/static/temp",
  "contents": {
    "a1b2c3d4": ["slide_1.png", "slide_2.png", "slide_3.png"],
    "e5f6g7h8": ["slide_1.png", "slide_2.png"]
  },
  "abs_path": "/app/static/temp",
  "exists": true,
  "is_dir": true
}
```

| Field | Type | Description |
|-------|------|-------------|
| `temp_dir` | string | The configured temporary directory path |
| `contents` | object | Map of carousel IDs to arrays of filenames |
| `abs_path` | string | Absolute path to the temporary directory |
| `exists` | boolean | Whether the directory exists |
| `is_dir` | boolean | Whether the path is a directory |

**Status Codes:**

| Code | Description |
|------|-------------|
| 200 | Success |
| 401 | Unauthorized - Invalid or missing API key |
| 500 | Server error |

### System Information

#### Health Check

Checks if the API is functioning correctly.

```
GET /health
```

**Authentication:**
No authentication required.

**Response:**

```json
{
  "status": "healthy",
  "timestamp": "2025-03-22T10:30:45.123456",
  "version": "1.0.0",
  "api_version": "v1",
  "system": {
    "cpu_usage": 15.2,
    "memory_usage": 45.7,
    "disk_usage": 32.1
  }
}
```

| Field | Type | Description |
|-------|------|-------------|
| `status` | string | Current health status |
| `timestamp` | string | Current server time in ISO format |
| `version` | string | API version |
| `api_version` | string | API version string |
| `system` | object | System resource metrics (if enabled) |

**Status Codes:**

| Code | Description |
|------|-------------|
| 200 | Success |
| 500 | Server error |

#### API Info

Retrieves API version information.

```
GET /api-info
```

**Authentication:**
No authentication required.

**Response:**

```json
{
  "api_name": "Instagram Carousel Generator",
  "api_version": "1.0.0",
  "available_versions": ["v1"],
  "latest_version": "v1",
  "documentation_url": "http://localhost:5001/docs"
}
```

| Field | Type | Description |
|-------|------|-------------|
| `api_name` | string | Name of the API |
| `api_version` | string | Current API version |
| `available_versions` | array | List of available API versions |
| `latest_version` | string | Latest API version |
| `documentation_url` | string | URL to the API documentation |

**Status Codes:**

| Code | Description |
|------|-------------|
| 200 | Success |
| 500 | Server error |

#### Metrics

Retrieves API metrics data.

```
GET /metrics
```

**Authentication:**
Requires an API key.

**Response:**

```json
{
  "timestamp": "2025-03-22T10:35:12.987654",
  "uptime": 86400,
  "requests": {
    "active": 2,
    "total": 1500,
    "errors": 25
  },
  "carousels": {
    "count": 75,
    "generated_today": 25
  },
  "system": {
    "cpu_usage": 15.2,
    "memory_usage": 45.7,
    "disk_usage": 32.1
  }
}
```

| Field | Type | Description |
|-------|------|-------------|
| `timestamp` | string | Current server time in ISO format |
| `uptime` | number | Server uptime in seconds |
| `requests` | object | Request metrics |
| `carousels` | object | Carousel generation metrics |
| `system` | object | System resource metrics |

**Status Codes:**

| Code | Description |
|------|-------------|
| 200 | Success |
| 401 | Unauthorized - Invalid or missing API key |
| 500 | Server error |

## Error Responses

All error responses follow a standard format:

```json
{
  "detail": "Error message description",
  "status_code": 400,
  "error_type": "ValidationError"
}
```

| Field | Type | Description |
|-------|------|-------------|
| `detail` | string | Human-readable error message |
| `status_code` | number | HTTP status code |
| `error_type` | string | Type of error that occurred |

## Rate Limiting

The API implements rate limiting to prevent abuse. Headers provide information about rate limits:

```
X-Rate-Limit-Limit: 100
X-Rate-Limit-Remaining: 95
X-Rate-Limit-Reset: 30
```

| Header | Description |
|--------|-------------|
| `X-Rate-Limit-Limit` | Maximum requests allowed in the current window |
| `X-Rate-Limit-Remaining` | Remaining requests in the current window |
| `X-Rate-Limit-Reset` | Seconds until the rate limit resets |

When a rate limit is exceeded, the API responds with status code `429 Too Many Requests` and the message:

```json
{
  "detail": "Rate limit exceeded: 100 requests per 60 seconds"
}
```

## Versioning

The API uses URL-based versioning with the current version being `v1`. All endpoints include the version in the URL path (e.g., `/api/v1/generate-carousel`).

When a version is deprecated, the API will include the following headers in responses:

```
Deprecation: 2025-07-15
Sunset: 2026-01-15
Link: </docs#tag/v2-endpoints>; rel="alternate"; title="Latest API version"
```

| Header | Description |
|--------|-------------|
| `Deprecation` | Date when the version was deprecated |
| `Sunset` | Date when the version will be removed |
| `Link` | Link to documentation for the latest version |

## Pagination

For endpoints that return lists of resources, the API supports pagination using the `limit` and `offset` query parameters:

```
GET /api/v1/resources?limit=10&offset=20
```

| Parameter | Description |
|-----------|-------------|
| `limit` | Maximum number of items to return (default: 50, max: 100) |
| `offset` | Number of items to skip (default: 0) |

Pagination information is included in the response:

```json
{
  "items": [...],
  "pagination": {
    "total": 100,
    "limit": 10,
    "offset": 20,
    "next": "/api/v1/resources?limit=10&offset=30",
    "previous": "/api/v1/resources?limit=10&offset=10"
  }
}
```

## Next Steps

Now that you're familiar with the API endpoints, you can:

1. Try the [Basic Usage Tutorial](tutorials/basic-usage.md) for practical examples
2. Learn about [Customizing Carousel Styling](tutorials/customizing-styling.md)
3. See how to [Integrate with Automation Workflows](tutorials/automation-integration.md)
