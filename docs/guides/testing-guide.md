# Testing Guide for Instagram Carousel Generator

This guide describes the testing strategy and practices used in the Instagram Carousel Generator project. It explains how to run the tests, how to write new tests, and the different types of tests used in the project.

## Table of Contents

1. [Test Organization](#test-organization)
2. [Running Tests](#running-tests)
3. [Test Categories](#test-categories)
4. [Testing Tools](#testing-tools)
5. [Writing Tests](#writing-tests)
6. [Continuous Integration](#continuous-integration)
7. [Test Coverage](#test-coverage)
8. [Best Practices](#best-practices)

## Test Organization

Tests are organized in the `tests/` directory at the project root. The directory structure mirrors the application structure, with test files prefixed with `test_`.

```
tests/
  ├─ conftest.py                   # Shared pytest fixtures
  ├─ test_api.py                   # API endpoint tests
  ├─ test_dependencies.py          # Integration tests for dependencies
  ├─ test_dependencies_unit.py     # Unit tests for dependency functions
  ├─ test_image_service.py         # Basic tests for image service
  ├─ test_image_service_parametrized.py  # Parameterized tests
  ├─ test_service_provider.py      # Service provider tests
  └─ test_storage_integration.py   # Storage service integration tests
```

## Running Tests

### Basic Test Execution

To run all tests:

```bash
pytest
```

To run a specific test file:

```bash
pytest tests/test_api.py
```

To run a specific test:

```bash
pytest tests/test_api.py::TestHealthAndInfo::test_health_check
```

### Running with Coverage

To run tests with coverage reporting:

```bash
pytest --cov=app tests/
```

For a detailed HTML coverage report:

```bash
pytest --cov=app --cov-report=html tests/
```

### Test Categories

Tests are categorized with markers to allow selective execution:

```bash
# Run only unit tests
pytest -m unit

# Run only integration tests
pytest -m integration

# Run only API tests
pytest -m api

# Run all tests except slow ones
pytest -m "not slow"
```

## Test Categories

The testing strategy includes several types of tests:

### Unit Tests

Unit tests verify the functionality of individual components in isolation, typically mocking any dependencies. These tests should be fast and focus on a small unit of code.

Example: `test_dependencies_unit.py` tests the individual dependency functions.

### Integration Tests

Integration tests verify that multiple components work correctly together. These tests may use real dependencies or a mix of real and mocked components.

Example: `test_storage_integration.py` tests the storage service's interaction with the file system.

### API Tests

API tests verify that the API endpoints work correctly from the client's perspective. These tests use the FastAPI TestClient to simulate HTTP requests.

Example: `test_api.py` tests the API endpoints.

### Parameterized Tests

Parameterized tests run the same test function with different inputs, allowing comprehensive testing of edge cases more efficiently.

Example: `test_image_service_parametrized.py` demonstrates testing image processing with different inputs.

## Testing Tools

The project uses the following testing tools:

- **pytest**: The core testing framework
- **pytest-cov**: For test coverage reporting
- **pytest-asyncio**: For testing asynchronous code
- **FastAPI TestClient**: For testing API endpoints
- **unittest.mock**: For mocking dependencies

## Writing Tests

### Fixtures

Use fixtures in `conftest.py` to set up shared test dependencies. This promotes test modularity and reduces duplication.

```python
@pytest.fixture
def test_image():
    """Create test image data."""
    return {
        'carousel_title': 'Test Carousel',
        'slides': [
            {'text': 'This is slide 1'},
            {'text': 'This is slide 2'}
        ],
        'include_logo': False,
        'logo_path': None
    }
```

### Test Classes

Organize tests in classes to group related tests. Use descriptive class and function names:

```python
class TestCarouselGeneration:
    """Tests for carousel generation endpoints."""
    
    def test_generate_carousel_with_mocks(self, client_with_mocks, carousel_request_data):
        """Test the carousel generation endpoint with mocked services."""
        # Test implementation...
```

### Mocking

Use mocks to isolate the component under test from its dependencies:

```python
@pytest.fixture
def mock_image_service():
    """Create a mock image service for testing."""
    mock_service = MagicMock(spec=BaseImageService)
    mock_service.create_carousel_images.return_value = [
        {"filename": "slide_1.png", "content": "fake_hex_content"}
    ]
    return mock_service
```

### Parameterization

Use parameterized tests for testing multiple inputs efficiently:

```python
@pytest.mark.parametrize("special_text,expected_replacements", [
    ("Text with arrow →", "->"),
    ("Text with quotes "quoted"", "\"quoted\""),
    ("Text with dash —", "-"),
])
def test_text_sanitization(self, enhanced_image_service, special_text, expected_replacements):
    """Test text sanitization with various special characters."""
    sanitized = enhanced_image_service.sanitize_text(special_text)
    assert expected_replacements in sanitized
```

## Continuous Integration

Tests are automatically run on push and pull requests using GitHub Actions. The workflow is defined in `.github/workflows/test.yml`.

## Test Coverage

The project aims for high test coverage, with a minimum of 85% line coverage. Coverage reports are generated during CI runs and can be viewed in the GitHub Actions artifacts.

## Best Practices

1. **Write Tests First**: Consider using Test-Driven Development (TDD) by writing tests before implementation.

2. **Single Assertion Principle**: Each test should verify one specific behavior. Tests with multiple assertions are harder to debug.

3. **Independent Tests**: Tests should not depend on each other's state. Each test should clean up after itself.

4. **Fast Tests**: Tests should run quickly. Slow tests discourage frequent testing.

5. **Mock External Dependencies**: Use mocks for external services to make tests reliable and fast.

6. **Meaningful Assertions**: Assertions should test meaningful behaviors, not implementation details.

7. **Test Error Cases**: Test both happy paths and error conditions.

8. **Consistent Naming**: Use consistent naming patterns for test files and functions.

9. **Keep CI Green**: Never merge code that breaks the tests. Fix broken tests immediately.

10. **Refactor Tests**: Refactor tests as needed to keep them clear and maintainable.