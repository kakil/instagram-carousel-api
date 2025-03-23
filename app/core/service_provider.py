"""
Service provider for dependency injection in the Instagram Carousel Generator.

This module acts as a service provider/container for implementing dependency injection pattern.
It provides a central place for registering and retrieving service instances,
making it easier to manage service lifecycles and dependencies.
"""

from typing import Dict, Any, Type, Callable, TypeVar, Optional, cast
import inspect
import logging

logger = logging.getLogger(__name__)

# Type variable for service types
T = TypeVar('T')


class ServiceProvider:
    """
    A simple service provider implementation for dependency injection.

    This class manages service registrations and their instantiation,
    supporting singleton and transient service lifetimes.
    """

    def __init__(self):
        """Initialize the service provider."""
        self._services: Dict[Type, Dict[str, Any]] = {}
        self._instances: Dict[Type, Dict[str, Any]] = {}

    def register(self, service_type: Type[T], factory: Callable[[], T],
                 singleton: bool = True):
        """
        Register a service with the provider.

        Args:
            service_type: The type of service to register
            factory: A factory function that creates the service
            singleton: Whether the service should be a singleton (default: True)
        """
        service_key = service_type.__name__

        if service_type not in self._services:
            self._services[service_type] = {}

        self._services[service_type][service_key] = {
            'factory': factory,
            'singleton': singleton
        }

        logger.debug(
            f"Registered service: {service_key} (singleton={singleton})")

    def register_instance(self, service_type: Type[T], instance: T):
        """
        Register an existing instance as a singleton service.

        Args:
            service_type: The type of service to register
            instance: The instance to register
        """
        service_key = service_type.__name__

        if service_type not in self._instances:
            self._instances[service_type] = {}

        self._instances[service_type][service_key] = instance
        logger.debug(f"Registered instance: {service_key}")

    def get(self, service_type: Type[T], key: Optional[str] = None) -> T:
        """
        Get an instance of the requested service.

        Args:
            service_type: The type of service to get
            key: Optional key for when multiple implementations of the same type exist

        Returns:
            An instance of the requested service

        Raises:
            KeyError: If the service is not registered
        """
        service_key = key or service_type.__name__

        # Check if we already have an instance (singleton case)
        if service_type in self._instances and service_key in self._instances[
            service_type]:
            return cast(T, self._instances[service_type][service_key])

        # Check if we have a registration for this service
        if service_type in self._services and service_key in self._services[
            service_type]:
            service_info = self._services[service_type][service_key]
            instance = service_info['factory']()

            # If singleton, store the instance
            if service_info['singleton']:
                if service_type not in self._instances:
                    self._instances[service_type] = {}
                self._instances[service_type][service_key] = instance

            return cast(T, instance)

        raise KeyError(f"Service not registered: {service_type.__name__}")

    def clear(self):
        """Clear all service registrations and instances."""
        self._services.clear()
        self._instances.clear()
        logger.debug("Cleared all service registrations and instances")


# Create a global instance of the service provider
provider = ServiceProvider()


# Export a function to get the global provider
def get_service_provider() -> ServiceProvider:
    """
    Get the global service provider instance.

    Returns:
        ServiceProvider: The global service provider
    """
    return provider