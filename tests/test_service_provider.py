"""
Tests for the service provider dependency injection system.

This module tests the functionality of the service provider pattern
and dependency injection system implemented in the application.
"""

import pytest
from unittest.mock import MagicMock, patch
from typing import Dict, Any, Type, TypeVar

from app.core.service_provider import ServiceProvider, get_service_provider
from app.core.services_setup import get_service
from app.services.image_service import BaseImageService


class TestServiceProvider:
    """Tests for the ServiceProvider class."""
    
    @pytest.fixture
    def empty_provider(self):
        """Create an empty service provider for testing."""
        return ServiceProvider()
        
    @pytest.fixture
    def test_service(self):
        """Create a test service class."""
        class TestService:
            def __init__(self, name="default"):
                self.name = name
                
            def get_name(self):
                return self.name
        
        return TestService
    
    def test_service_provider_init(self, empty_provider):
        """Test initialization of service provider."""
        assert hasattr(empty_provider, '_services')
        assert hasattr(empty_provider, '_instances')
        assert empty_provider._services == {}
        assert empty_provider._instances == {}
    
    def test_register_singleton_service(self, empty_provider, test_service):
        """Test registering a singleton service."""
        # Create a factory function
        def factory():
            return test_service("test_singleton")
        
        # Register the service
        empty_provider.register(test_service, factory, singleton=True)
        
        # Verify it was registered
        assert test_service in empty_provider._services
        assert test_service.__name__ in empty_provider._services[test_service]
        assert empty_provider._services[test_service][test_service.__name__]["singleton"] is True
        
        # Get the service twice and verify it's the same instance
        service1 = empty_provider.get(test_service)
        service2 = empty_provider.get(test_service)
        
        assert service1 is service2
        assert service1.get_name() == "test_singleton"
        
        # Verify the instance was cached
        assert test_service in empty_provider._instances
        assert test_service.__name__ in empty_provider._instances[test_service]
    
    def test_register_transient_service(self, empty_provider, test_service):
        """Test registering a transient service."""
        # Create a factory function
        counter = 0
        def factory():
            nonlocal counter
            counter += 1
            return test_service(f"test_transient_{counter}")
        
        # Register the service
        empty_provider.register(test_service, factory, singleton=False)
        
        # Verify it was registered
        assert test_service in empty_provider._services
        assert test_service.__name__ in empty_provider._services[test_service]
        assert empty_provider._services[test_service][test_service.__name__]["singleton"] is False
        
        # Get the service twice and verify it's different instances
        service1 = empty_provider.get(test_service)
        service2 = empty_provider.get(test_service)
        
        assert service1 is not service2
        assert service1.get_name() == "test_transient_1"
        assert service2.get_name() == "test_transient_2"
        
        # Verify no instance was cached
        assert test_service not in empty_provider._instances or \
               test_service.__name__ not in empty_provider._instances.get(test_service, {})
    
    def test_register_instance(self, empty_provider, test_service):
        """Test registering an existing instance."""
        # Create an instance
        instance = test_service("test_instance")
        
        # Register the instance
        empty_provider.register_instance(test_service, instance)
        
        # Verify it was registered directly in the instances
        assert test_service in empty_provider._instances
        assert test_service.__name__ in empty_provider._instances[test_service]
        assert empty_provider._instances[test_service][test_service.__name__] is instance
        
        # Get the service and verify it's the same instance
        service = empty_provider.get(test_service)
        assert service is instance
        assert service.get_name() == "test_instance"
    
    def test_get_service_nonexistent(self, empty_provider):
        """Test getting a non-existent service raises KeyError."""
        class NonExistentService:
            pass
        
        with pytest.raises(KeyError):
            empty_provider.get(NonExistentService)
    
    def test_register_multiple_services_same_type(self, empty_provider, test_service):
        """Test registering multiple services with the same type but different keys."""
        # Register two services with the same type but different keys
        empty_provider.register(test_service, lambda: test_service("service1"), singleton=True)
        
        # Now manually register another service with a different key
        if test_service not in empty_provider._services:
            empty_provider._services[test_service] = {}
            
        empty_provider._services[test_service]["service2"] = {
            "factory": lambda: test_service("service2"),
            "singleton": True
        }
        
        # Get both services by different keys
        service1 = empty_provider.get(test_service)  # Default key (class name)
        service2 = empty_provider.get(test_service, key="service2")
        
        assert service1 is not service2
        assert service1.get_name() == "service1"
        assert service2.get_name() == "service2"
    
    def test_clear_services(self, empty_provider, test_service):
        """Test clearing services."""
        # Register some services
        empty_provider.register(test_service, lambda: test_service("service1"), singleton=True)
        empty_provider.register_instance(test_service, test_service("service2"))
        
        # Verify services are registered
        assert test_service in empty_provider._services
        assert test_service in empty_provider._instances
        
        # Clear services
        empty_provider.clear()
        
        # Verify services are cleared
        assert empty_provider._services == {}
        assert empty_provider._instances == {}


class TestServiceProviderIntegration:
    """Tests for the service provider integration with the application."""
    
    def test_get_service_provider_global(self):
        """Test the global service provider is a singleton."""
        provider1 = get_service_provider()
        provider2 = get_service_provider()
        
        assert provider1 is provider2
        assert isinstance(provider1, ServiceProvider)
    
    def test_get_service_integration(self):
        """Test getting a service through the get_service function."""
        # This depends on the service being registered correctly
        # We should mock the provider to avoid side effects
        with patch('app.core.services_setup.get_service_provider') as mock_get_provider:
            mock_provider = MagicMock()
            mock_get_provider.return_value = mock_provider
            
            mock_service = MagicMock()
            mock_provider.get.return_value = mock_service
            
            # Call get_service
            result = get_service(BaseImageService, key="TestKey")
            
            # Verify the provider was called correctly
            mock_provider.get.assert_called_once_with(BaseImageService, "TestKey")
            assert result is mock_service