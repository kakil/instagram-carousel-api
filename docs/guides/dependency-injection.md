# Dependency Injection Guide

## Overview

This guide explains the dependency injection pattern as implemented in the Instagram Carousel Generator project. Dependency injection is a design pattern that helps to create loosely coupled, maintainable, and testable code by explicitly providing (injecting) dependencies to components rather than having components create or find their dependencies.

## Benefits of Dependency Injection

- **Testability**: Makes unit testing easier by allowing dependencies to be mocked
- **Modularity**: Services can be easily swapped out for different implementations
- **Maintainability**: Reduces tight coupling between components
- **Reusability**: Services can be reused across different components
- **Configurability**: Application behavior can be changed by providing different implementations

## How Dependency Injection Works in Our Project

Our implementation of dependency injection uses a three-tier approach:

1. **FastAPI's Built-in Dependency Injection System**: For HTTP request-scoped dependencies
2. **Centralized Dependencies Module**: For organizing and providing dependencies
3. **Service Provider Pattern**: For managing service lifetimes and registrations

### Key Components

#### 1. `app/api/dependencies.py`

This module provides FastAPI dependency functions for various services and components. It acts as the bridge between the FastAPI dependency injection system and our services.

Example usage in an endpoint:

```python
@router.post("/generate-carousel")
async def generate_carousel(
    request: CarouselRequest,
    image_service: BaseImageService = Depends(get_enhanced_image_service),
    storage_service: StorageService = Depends(get_storage_service)
):
    # Use the injected services
    result = image_service.create_carousel_images(...)
    # ...
```

#### 2. `app/core/service_provider.py`

This module implements a simple service provider (IoC container) to manage service registrations and instances. It supports both singleton and transient service lifetimes.

Example registering services:

```python
provider = get_service_provider()
provider.register(
    BaseImageService,
    lambda: get_image_service(ImageServiceType.ENHANCED.value, image_settings),
    singleton=True
)
```

Example using the service provider:

```python
provider = get_service_provider()
image_service = provider.get(BaseImageService)
```

#### 3. `app/core/services_setup.py`

This module handles the registration of all application services during startup. It ensures that all required services are properly registered before the application begins handling requests.

## Service Lifecycles

Our implementation supports two service lifecycles:

1. **Singleton**: One instance per application (default)
   - Appropriate for stateless services or services that manage their own state
   - Lower memory usage, created once at startup

2. **Transient**: New instance each time it's requested
   - Appropriate for services that need a fresh state for each use
   - Higher memory usage, created on-demand

## Using Dependency Injection in Endpoints

To use a dependency in an endpoint:

1. Import the dependency function from `app.api.dependencies`
2. Use FastAPI's `Depends()` to inject the dependency

```python
from fastapi import Depends
from app.api.dependencies import get_enhanced_image_service

@router.post("/my-endpoint")
async def my_endpoint(
    image_service = Depends(get_enhanced_image_service)
):
    # Use image_service here
    pass
```

## Creating New Dependencies

To create a new dependency:

1. Add a new function in `app/api/dependencies.py` that returns your service
2. If needed, register your service in `app/core/services_setup.py`
3. Use the dependency in your endpoints with `Depends()`

Example:

```python
# In app/api/dependencies.py
def get_my_service() -> MyService:
    """Provide MyService instance"""
    return my_service_instance

# In your endpoint
@router.post("/endpoint")
async def endpoint(
    my_service = Depends(get_my_service)
):
    # Use my_service
    pass
```

## Testing with Dependency Injection

One of the main benefits of dependency injection is easier testing. You can override dependencies in tests to provide mocks instead of real implementations.

Example:

```python
# In your test file
def test_endpoint(client):
    # Create mock service
    mock_service = MagicMock(spec=MyService)
    
    # Override the dependency
    app.dependency_overrides[get_my_service] = lambda: mock_service
    
    # Test with the mock
    response = client.post("/endpoint", json={...})
    
    # Verify
    assert response.status_code == 200
    mock_service.some_method.assert_called_once()
    
    # Clean up
    app.dependency_overrides = {}
```

See `tests/test_dependencies.py` for complete examples of testing with mocked dependencies.

## Best Practices

1. **Always use interfaces/abstract classes**: Inject abstract interfaces rather than concrete implementations to maintain flexibility.

2. **Keep dependencies explicit**: Don't hide dependencies by retrieving them inside methods.

3. **Minimize side effects**: Dependencies should be well-behaved and predictable.

4. **Use meaningful dependency names**: Dependency functions should clearly indicate what they provide.

5. **Prefer constructor injection**: When designing classes, prefer receiving dependencies in the constructor.

6. **Document dependencies**: Clearly document what each service does and its lifecycle.

7. **Test with mocks**: Always test endpoints with mocked dependencies to ensure isolation.

## Examples

### Standard Endpoint with Dependencies

```python
@router.post("/generate-carousel", response_model=CarouselResponse)
async def generate_carousel(
    request: CarouselRequest,
    background_tasks: BackgroundTasks,
    image_service: BaseImageService = Depends(get_enhanced_image_service),
    storage_service: StorageService = Depends(get_storage_service),
    _: None = Depends(get_heavy_rate_limit)
):
    # Implementation using injected services
    result = image_service.create_carousel_images(
        request.carousel_title,
        request.slides,
        carousel_id
    )
    # ...
```

### Creating a Custom Service Implementation

```python
class CustomImageService(BaseImageService):
    """Custom image service implementation"""
    # Implementation here...

# In app/core/services_setup.py
provider.register(
    BaseImageService,
    lambda: CustomImageService(settings),
    singleton=True
)

# Access in dependencies.py
def get_custom_image_service() -> BaseImageService:
    provider = get_service_provider()
    return provider.get(BaseImageService, key="CustomImageService")
```

### Testing with Mocked Dependencies

```python
def test_with_mocked_dependencies(client):
    # Create mocks
    mock_image_service = MagicMock(spec=BaseImageService)
    mock_storage_service = MagicMock(spec=StorageService)
    
    # Configure mocks
    mock_image_service.create_carousel_images.return_value = [
        {"filename": "test.png", "content": "test_content"}
    ]
    
    # Override dependencies
    app.dependency_overrides = {
        get_enhanced_image_service: lambda: mock_image_service,
        get_storage_service: lambda: mock_storage_service
    }
    
    # Test with mocks
    response = client.post("/api/v1/generate-carousel", json={...})
    
    # Verify
    assert response.status_code == 200
    mock_image_service.create_carousel_images.assert_called_once()
    
    # Clean up
    app.dependency_overrides = {}
```