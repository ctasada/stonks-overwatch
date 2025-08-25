"""
Authentication service factory with dependency injection support.

This module provides a factory for creating authentication services with proper
dependency injection and lifecycle management, following the same patterns used
for broker services.
"""

from typing import Dict, Optional, Type

from stonks_overwatch.core.exceptions import StonksOverwatchException
from stonks_overwatch.core.interfaces.authentication_service import AuthenticationServiceInterface
from stonks_overwatch.core.interfaces.credential_service import CredentialServiceInterface
from stonks_overwatch.core.interfaces.session_manager import SessionManagerInterface
from stonks_overwatch.utils.core.logger import StonksLogger
from stonks_overwatch.utils.core.singleton import singleton


class AuthenticationFactoryError(StonksOverwatchException):
    """Exception raised for authentication factory errors."""

    pass


# Constants
_NOT_REGISTERED = "Not registered"


@singleton
class AuthenticationFactory:
    """
    Factory for creating authentication services with dependency injection.

    This singleton factory manages the creation and lifecycle of authentication
    services, providing dependency injection and caching capabilities.
    """

    def __init__(self):
        """Initialize the authentication factory."""
        self.logger = StonksLogger.get_logger("stonks_overwatch.core", "[AUTH_FACTORY]")

        # Service type registrations
        self._session_manager_class: Optional[Type[SessionManagerInterface]] = None
        self._credential_service_class: Optional[Type[CredentialServiceInterface]] = None
        self._authentication_service_class: Optional[Type[AuthenticationServiceInterface]] = None

        # Service instances for caching
        self._session_manager_instance: Optional[SessionManagerInterface] = None
        self._credential_service_instance: Optional[CredentialServiceInterface] = None
        self._authentication_service_instance: Optional[AuthenticationServiceInterface] = None

        # Cache control
        self._cache_enabled = True

    def register_session_manager(self, session_manager_class: Type[SessionManagerInterface]) -> None:
        """
        Register the session manager class.

        Args:
            session_manager_class: The session manager class to register
        """
        self._session_manager_class = session_manager_class
        self.logger.debug(f"Registered session manager: {session_manager_class.__name__}")

    def register_credential_service(self, credential_service_class: Type[CredentialServiceInterface]) -> None:
        """
        Register the credential service class.

        Args:
            credential_service_class: The credential service class to register
        """
        self._credential_service_class = credential_service_class
        self.logger.debug(f"Registered credential service: {credential_service_class.__name__}")

    def register_authentication_service(
        self, authentication_service_class: Type[AuthenticationServiceInterface]
    ) -> None:
        """
        Register the authentication service class.

        Args:
            authentication_service_class: The authentication service class to register
        """
        self._authentication_service_class = authentication_service_class
        self.logger.debug(f"Registered authentication service: {authentication_service_class.__name__}")

    def create_session_manager(self, config=None, **kwargs) -> SessionManagerInterface:
        """
        Create a session manager instance.

        Args:
            config: Optional configuration for dependency injection
            **kwargs: Additional arguments to pass to constructor

        Returns:
            SessionManagerInterface: The session manager instance

        Raises:
            AuthenticationFactoryError: If session manager class is not registered
        """
        if self._session_manager_class is None:
            raise AuthenticationFactoryError("No session manager class registered")

        if self._cache_enabled and self._session_manager_instance is not None:
            return self._session_manager_instance

        try:
            instance = self._session_manager_class(config, **kwargs)

            if self._cache_enabled:
                self._session_manager_instance = instance
                self.logger.debug("Created and cached session manager instance")
            else:
                self.logger.debug("Created session manager instance")

            return instance
        except Exception as e:
            self.logger.error(f"Failed to create session manager: {e}")
            raise AuthenticationFactoryError(f"Failed to create session manager: {e}") from e

    def create_credential_service(self, config=None, **kwargs) -> CredentialServiceInterface:
        """
        Create a credential service instance.

        Args:
            config: Optional configuration for dependency injection
            **kwargs: Additional arguments to pass to constructor

        Returns:
            CredentialServiceInterface: The credential service instance

        Raises:
            AuthenticationFactoryError: If credential service class is not registered
        """
        if self._credential_service_class is None:
            raise AuthenticationFactoryError("No credential service class registered")

        if self._cache_enabled and self._credential_service_instance is not None:
            return self._credential_service_instance

        try:
            instance = self._credential_service_class(config, **kwargs)

            if self._cache_enabled:
                self._credential_service_instance = instance
                self.logger.debug("Created and cached credential service instance")
            else:
                self.logger.debug("Created credential service instance")

            return instance
        except Exception as e:
            self.logger.error(f"Failed to create credential service: {e}")
            raise AuthenticationFactoryError(f"Failed to create credential service: {e}") from e

    def create_authentication_service(self, config=None, **kwargs) -> AuthenticationServiceInterface:
        """
        Create an authentication service instance with dependency injection.

        This method automatically injects the session manager and credential service
        dependencies if they are not provided in kwargs.

        Args:
            config: Optional configuration for dependency injection
            **kwargs: Additional arguments to pass to constructor

        Returns:
            AuthenticationServiceInterface: The authentication service instance

        Raises:
            AuthenticationFactoryError: If authentication service class is not registered
        """
        if self._authentication_service_class is None:
            raise AuthenticationFactoryError("No authentication service class registered")

        if self._cache_enabled and self._authentication_service_instance is not None:
            return self._authentication_service_instance

        try:
            # Automatic dependency injection
            if "session_manager" not in kwargs:
                kwargs["session_manager"] = self.create_session_manager(config)
                self.logger.debug("Injected session manager into authentication service")

            if "credential_service" not in kwargs:
                kwargs["credential_service"] = self.create_credential_service(config)
                self.logger.debug("Injected credential service into authentication service")

            # Pass config as well
            kwargs["config"] = config

            instance = self._authentication_service_class(**kwargs)

            if self._cache_enabled:
                self._authentication_service_instance = instance
                self.logger.debug("Created and cached authentication service instance")
            else:
                self.logger.debug("Created authentication service instance")

            return instance
        except Exception as e:
            self.logger.error(f"Failed to create authentication service: {e}")
            raise AuthenticationFactoryError(f"Failed to create authentication service: {e}") from e

    def get_authentication_service(self, config=None) -> AuthenticationServiceInterface:
        """
        Get the authentication service instance (creating if necessary).

        This is the main entry point for accessing the authentication service
        throughout the application.

        Args:
            config: Optional configuration for dependency injection

        Returns:
            AuthenticationServiceInterface: The authentication service instance
        """
        return self.create_authentication_service(config)

    def clear_cache(self) -> None:
        """Clear all cached service instances."""
        self._session_manager_instance = None
        self._credential_service_instance = None
        self._authentication_service_instance = None
        self.logger.debug("Cleared authentication service cache")

    def set_cache_enabled(self, enabled: bool) -> None:
        """
        Enable or disable service caching.

        Args:
            enabled: Whether to enable caching
        """
        self._cache_enabled = enabled
        if not enabled:
            self.clear_cache()
        self.logger.debug(f"Set cache enabled: {enabled}")

    def is_fully_registered(self) -> bool:
        """
        Check if all required services are registered.

        Returns:
            bool: True if all services are registered, False otherwise
        """
        return (
            self._session_manager_class is not None
            and self._credential_service_class is not None
            and self._authentication_service_class is not None
        )

    def get_registered_services(self) -> Dict[str, str]:
        """
        Get information about registered services.

        Returns:
            Dict[str, str]: Dictionary of service types to class names
        """
        return {
            "session_manager": self._session_manager_class.__name__ if self._session_manager_class else _NOT_REGISTERED,
            "credential_service": self._credential_service_class.__name__
            if self._credential_service_class
            else _NOT_REGISTERED,
            "authentication_service": self._authentication_service_class.__name__
            if self._authentication_service_class
            else _NOT_REGISTERED,
        }
