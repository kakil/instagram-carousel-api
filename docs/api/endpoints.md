# Instagram Carousel Generator API Documentation

This document describes the API endpoints available in the Instagram Carousel Generator. The API is built with FastAPI and follows RESTful design principles.

## Base URL

```
http://localhost:5001/api/v1
```

For production deployments, replace with your domain:

```
https://api.yourdomain.com/api/v1
```

## Authentication

In production environments, API requests should include an API key in the header:

```
X-API-Key: your-api-key
```

## Endpoints

### Health Check

Check the API health status.

**URL**: `/health`  
**Method**: `GET`  
**Auth required**: No

#### Success Response

```json
{
  "status": "healthy",
  "timestamp": "2025-03-22T10:30:45.123456",
  "version": "1.0.0"
}
```

### Generate Carousel

Generate carousel images from text content.

**URL**: `/generate-carousel`  
**Method**: `POST`  
**Auth required**: Yes (in production)  
**Content-Type**: `application/json`

#### Request Body

```json
{
  "carousel_title": "5 Productivity Tips",
  "slides": [
    {"text": "Wake up early and plan your day"},
    {"text": "Use the Pomodoro technique for focus"},
    {"text": "Take regular breaks to recharge"}
  ],
  "include_logo": true,
  "logo_path": "static/assets/logo.png",
  "settings": {
    "width": 1080,
    "height": 1080,
    "bg_color": [18, 18, 18]
  }
}
```

##### Parameters

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| carousel_title | string | Yes | Title for the carousel (shown on first slide) |
| slides | array | Yes | Array of slide objects with text content |
| include_logo | boolean | No | Whether to include a logo (default: false) |
| logo_path | string | No | Path to logo file (required if include_logo is true) |
| settings | object | No | Custom settings for image generation |

##### Settings Object

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| width | integer | No | Width of carousel images in pixels |
| height | integer | No | Height of carousel images in pixels |
| bg_color | array | No | Background color as RGB tuple [r, g, b] |

#### Success Response

**Code**: `200 OK`

```json
{
  "status": "success",
  "carousel_id": "abc12345",
  "slides": [
    {
      "filename": "slide_1.png",
      "content": "89504e470d0a1a0a..."  // Hex-encoded image content
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

#### Error Response

**Code**: `500 Internal Server Error`

```json
{
  "detail": "Error generating carousel: Error message details"
}
```

### Generate Carousel with URLs

Generate carousel images and return public URLs for accessing them.

**URL**: `/generate-carousel-with-urls`  
**Method**: `POST`  
**Auth required**: Yes (in production)  
**Content-Type**: `application/json`

#### Request Body

Same as `/generate-carousel` endpoint.

#### Success Response

**Code**: `200 OK`

```json
{
  "status": "success",
  "carousel_id": "abc12345",
  "slides": [
    {
      "filename": "slide_1.png",
      "content": "89504e470d0a1a0a..."  // Hex-encoded image content
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
    "https://api.example.com/api/v1/temp/abc12345/slide_1.png",
    "https://api.example.com/api/v1/temp/abc12345/slide_2.png",
    "https://api.example.com/api/v1/temp/abc12345/slide_3.png"
  ]
}
```

### Get Temporary File

Access a generated carousel image by its ID and filename.

**URL**: `/temp/{carousel_id}/{filename}`  
**Method**: `GET`  
**Auth required**: No  
**URL Parameters**:
- `carousel_id`: Unique identifier for the carousel
- `filename`: Name of the image file

#### Success Response

**Code**: `200 OK`  
**Content-Type**: `image/png` (or other appropriate image type)  
**Body**: Binary image data

#### Error Response

**Code**: `404 Not Found`

```json
{
  "detail": "File not found"
}
```

### Debug Temp Directory (Debug Only)

View contents of the temporary directory for debugging purposes.

**URL**: `/debug-temp`  
**Method**: `GET`  
**Auth required**: Yes (in production)

#### Success Response

**Code**: `200 OK`

```json
{
  "temp_dir": "/path/to/temp",
  "contents": {
    "abc12345": ["slide_1.png", "slide_2.png", "slide_3.png"],
    "def67890": ["slide_1.png", "slide_2.png"]
  },
  "abs_path": "/absolute/path/to/temp",
  "exists": true,
  "is_dir": true
}
```

## Status Codes

The API uses the following status codes:

- `200 OK`: Request was successful
- `400 Bad Request`: Invalid request parameters
- `401 Unauthorized`: API key is missing or invalid
- `404 Not Found`: Resource not found
- `429 Too Many Requests`: Rate limit exceeded
- `500 Internal Server Error`: Server error

## Rate Limiting

In production environments, API endpoints are rate-limited to prevent abuse:

- `/generate-carousel`: 10 requests per minute
- `/generate-carousel-with-urls`: 10 requests per minute

## File Lifetime

Temporary files created by the API have a limited lifetime (default: 24 hours) after which they are automatically deleted.
