# Core Concepts Guide

This guide explains the key architectural concepts and design patterns used in the Instagram Carousel Generator API. Understanding these concepts will help you use the API effectively and extend it for your own needs.

## System Architecture

The Instagram Carousel Generator follows a modular, service-oriented architecture designed with clean separation of concerns:

```
instagram_carousel_generator/
├── api/                # API endpoints and routing
│   ├── v1/             # Version 1 API implementation
│   ├── security.py     # Authentication and security
│   └── dependencies.py # FastAPI dependencies
├── core/               # Core configuration and models
│   ├── config.py       # Application settings
│   ├── models.py       # Data models
│   └── service_provider.py # Dependency injection container
├── services/           # Business logic services
│   ├── image_service/  # Image generation services
│   │   ├── base_image_service.py      # Abstract base class
│   │   ├── standard_image_service.py  # Standard implementation
│   │   └── enhanced_image_service.py  # Enhanced implementation
│   └── storage_service.py # File storage and management
└── utils/              # Utility functions and helpers
    ├── image_utils.py  # Image processing utilities
    └── logging.py      # Logging configuration
```

### Key Components

1. **API Layer**: Responsible for handling HTTP requests, input validation, and response formatting
2. **Services Layer**: Contains the core business logic
3. **Core Layer**: Provides configuration, models, and dependency management
4. **Utils Layer**: Offers reusable utility functions across the application

## Dependency Injection System

The API uses a custom dependency injection system via the `ServiceProvider` class, which manages service registrations and their instantiation. This approach:

- Makes components more testable by allowing mock services to be injected
- Promotes loose coupling between components
- Simplifies extending the system with new implementations

### How It Works

1. **Service Registration**:
   ```python
   # In services_setup.py
   provider.register(BaseImageService,
                    lambda: get_image_service(ImageServiceType.ENHANCED.value, settings),
                    singleton=True)
   provider.register_instance(StorageService, storage_service)
   ```

2. **Service Retrieval**:
   ```python
   # In API dependencies
   def get_enhanced_image_service() -> BaseImageService:
       return get_service(BaseImageService, key="EnhancedImageService")

   # In FastAPI endpoints
   @router.post("/generate-carousel")
   async def generate_carousel(
       request: CarouselRequest,
       image_service: BaseImageService = Depends(get_enhanced_image_service)
   ):
       # Use the injected image_service here
       result = image_service.create_carousel_images(...)
   ```

## Image Service Architecture

The image service follows a class hierarchy using the **Template Method** design pattern:

```
BaseImageService (Abstract Base Class)
├── StandardImageService
└── EnhancedImageService
```

- **BaseImageService**: Defines the interface and common utility methods
- **StandardImageService**: Basic implementation with core functionality
- **EnhancedImageService**: Advanced implementation with improved error handling and text rendering

### Factory Pattern

The system uses the Factory pattern to create the appropriate service implementation:

```python
def get_image_service(
    service_type: str = ImageServiceType.ENHANCED.value,
    settings: Optional[Dict[str, Any]] = None,
) -> BaseImageService:
    settings = settings or {}

    if service_type == ImageServiceType.STANDARD.value:
        return StandardImageService(settings)
    elif service_type == ImageServiceType.ENHANCED.value:
        return EnhancedImageService(settings)
    else:
        raise ValueError(f"Invalid image service type: {service_type}")
```

This approach makes it easy to add new service implementations without changing client code.

## API Versioning

The API uses URL-based versioning to ensure backward compatibility:

```
/api/v1/generate-carousel
```

All routes are organized by version, allowing the introduction of new versions without breaking existing clients. The versioning system:

- Ensures API stability for clients
- Allows gradual migration to newer versions
- Includes version-specific dependencies and middleware

### Version Lifecycle

Each API version goes through a defined lifecycle:

1. **Current**: The newest recommended version
2. **Supported**: Still fully supported but no longer the newest
3. **Deprecated**: Still works but scheduled for removal
4. **Sunset**: No longer available

The API provides headers to notify clients about version status:
```
Deprecation: 2025-03-15
Sunset: 2025-09-15
Link: </docs#tag/v2-endpoints>; rel="alternate"; title="Latest API version"
```

## Rate Limiting and Security

The API includes several security features:

1. **API Key Authentication**:
   ```python
   # In security.py
   def get_api_key(
       api_key_header: str = Security(api_key_header),
       api_key_query: str = Security(api_key_query),
   ) -> bool:
       # Validate API key
   ```

2. **Rate Limiting**:
   ```python
   # In security.py
   def rate_limit(max_requests: int = 100, window_seconds: int = 60) -> Callable:
       # Rate limiting implementation
   ```

3. **Path Validation**:
   ```python
   # Validate file access to prevent directory traversal
   def validate_file_access(carousel_id: str, filename: str) -> None:
       # Validation logic
   ```

## Monitoring and Performance Tracking

The API includes comprehensive monitoring:

1. **Structured Logging**: JSON-formatted logs with context information
2. **Performance Monitoring**: Timing for critical operations
3. **Request Tracking**: Unique IDs for each request to trace through the system
4. **Metrics Collection**: Collection of operational metrics for analysis

## Next Steps

Now that you understand the core concepts, you can:

1. Follow the [Basic Usage Tutorial](tutorials/basic-usage.md) for practical examples
2. Learn about [Customizing Carousel Styling](tutorials/customizing-styling.md)
3. See how to [Create Custom Image Service Implementations](tutorials/custom-image-service.md)
4. Explore the [API Reference](api-reference.md) for detailed endpoint information
