"""
Authentication service locator for optimized service access.

This module provides a high-performance service locator pattern for accessing
authentication services efficiently across the application without repeated
factory instantiation.
"""

from typing import Optional

from stonks_overwatch.core.factories.authentication_factory import AuthenticationFactory
from stonks_overwatch.core.interfaces.authentication_service import AuthenticationServiceInterface
from stonks_overwatch.utils.core.logger import StonksLogger


class AuthenticationServiceLocator:
    """
    Optimized service locator for authentication services.

    This class provides efficient access to authentication services with:
    - Cached factory instance
    - Pre-cached authentication service
    - Performance monitoring
    - Memory optimization
    """

    _factory_instance: Optional[AuthenticationFactory] = None
    _auth_service_instance: Optional[AuthenticationServiceInterface] = None
    _access_count = 0

    logger = StonksLogger.get_logger("stonks_overwatch.core", "[AUTH_LOCATOR]")

    @classmethod
    def get_authentication_service(cls, config=None) -> AuthenticationServiceInterface:
        """
        Get the authentication service instance with optimized caching.

        This method provides high-performance access to the authentication service
        by maintaining cached instances and avoiding repeated factory instantiation.

        Args:
            config: Optional configuration for dependency injection

        Returns:
            AuthenticationServiceInterface: The authentication service instance
        """
        cls._access_count += 1

        # Use cached service if available and no specific config requested
        if config is None and cls._auth_service_instance is not None:
            cls.logger.debug(f"Returning cached authentication service (access #{cls._access_count})")
            return cls._auth_service_instance

        # Get or create factory instance
        if cls._factory_instance is None:
            cls._factory_instance = AuthenticationFactory()
            cls.logger.debug("Created and cached authentication factory instance")

        # Get authentication service from factory
        auth_service = cls._factory_instance.get_authentication_service(config)

        # Cache the service if no specific config (default configuration)
        if config is None and cls._auth_service_instance is None:
            cls._auth_service_instance = auth_service
            cls.logger.debug("Cached authentication service for future access")

        cls.logger.debug(f"Provided authentication service (access #{cls._access_count})")
        return auth_service

    @classmethod
    def clear_cache(cls) -> None:
        """
        Clear all cached instances to free memory.

        This method should be called during application shutdown or when
        reconfiguration is needed.
        """
        if cls._factory_instance:
            cls._factory_instance.clear_cache()

        cls._factory_instance = None
        cls._auth_service_instance = None
        cls._access_count = 0

        cls.logger.info("Cleared authentication service locator cache")

    @classmethod
    def get_cache_status(cls) -> dict:
        """
        Get cache status information for monitoring and debugging.

        Returns:
            dict: Cache status information including access count and cached instances
        """
        return {
            "access_count": cls._access_count,
            "factory_cached": cls._factory_instance is not None,
            "auth_service_cached": cls._auth_service_instance is not None,
            "factory_services_registered": (
                cls._factory_instance.is_fully_registered() if cls._factory_instance else False
            ),
        }

    @classmethod
    def warmup_cache(cls) -> None:
        """
        Pre-warm the cache by creating service instances.

        This method can be called during application startup to ensure
        services are ready for immediate use, reducing first-access latency.
        """
        cls.logger.info("Warming up authentication service cache")

        # Create factory and authentication service
        auth_service = cls.get_authentication_service()

        cache_status = cls.get_cache_status()
        cls.logger.info(f"Cache warmup completed: {cache_status}")

        return auth_service


# Convenient module-level functions for easy access
def get_authentication_service(config=None) -> AuthenticationServiceInterface:
    """
    Module-level convenience function to get authentication service.

    Args:
        config: Optional configuration for dependency injection

    Returns:
        AuthenticationServiceInterface: The authentication service instance
    """
    return AuthenticationServiceLocator.get_authentication_service(config)


def clear_authentication_cache() -> None:
    """
    Module-level convenience function to clear authentication cache.
    """
    AuthenticationServiceLocator.clear_cache()


def get_authentication_cache_status() -> dict:
    """
    Module-level convenience function to get cache status.

    Returns:
        dict: Cache status information
    """
    return AuthenticationServiceLocator.get_cache_status()
