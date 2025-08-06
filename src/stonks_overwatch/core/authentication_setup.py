"""
Authentication service registration setup.

This module provides the registration setup for authentication services,
following the same pattern as broker service registration.
"""

from stonks_overwatch.core.factories.authentication_factory import AuthenticationFactory
from stonks_overwatch.services.utilities.authentication_credential_service import AuthenticationCredentialService
from stonks_overwatch.services.utilities.authentication_service import AuthenticationService
from stonks_overwatch.services.utilities.authentication_session_manager import AuthenticationSessionManager
from stonks_overwatch.utils.core.logger import StonksLogger


def register_authentication_services():
    """
    Register all authentication services with the authentication factory.

    This function sets up the dependency injection configuration for authentication
    services, registering concrete implementations with the factory.
    """
    logger = StonksLogger.get_logger("stonks_overwatch.core", "[AUTH_SETUP]")

    try:
        # Get the authentication factory instance
        auth_factory = AuthenticationFactory()

        # Register all authentication service implementations
        auth_factory.register_session_manager(AuthenticationSessionManager)
        auth_factory.register_credential_service(AuthenticationCredentialService)
        auth_factory.register_authentication_service(AuthenticationService)

        logger.info("Authentication services registered successfully")

        # Verify registration
        if auth_factory.is_fully_registered():
            registered_services = auth_factory.get_registered_services()
            logger.info(f"Registered authentication services: {registered_services}")
        else:
            logger.error("Not all authentication services were registered properly")

    except Exception as e:
        logger.error(f"Failed to register authentication services: {e}")
        raise e
