"""
General authentication middleware for Stonks Overwatch.

This middleware handles authentication logic that applies to all brokers,
not specific to any single broker implementation.
"""

from typing import Optional

from django.shortcuts import redirect
from django.urls import resolve

from stonks_overwatch.core.authentication_locator import get_authentication_service
from stonks_overwatch.core.factories.broker_factory import BrokerFactory
from stonks_overwatch.core.factories.broker_registry import BrokerRegistry
from stonks_overwatch.utils.core.constants import AuthenticationErrorMessages, LogMessages
from stonks_overwatch.utils.core.logger import StonksLogger
from stonks_overwatch.utils.core.session_keys import SessionKeys


class AuthenticationMiddleware:
    """
    General authentication middleware for all brokers.

    Handles:
    - Public URL access control
    - Broker configuration validation
    - Basic session authentication
    - Maintenance mode access
    """

    PUBLIC_URLS = {"login", "broker_login", "settings", "release_notes"}

    logger = StonksLogger.get_logger("stonks_overwatch.authentication", "[AUTH_MIDDLEWARE]")

    def __init__(self, get_response):
        self.get_response = get_response
        self.auth_service = get_authentication_service()
        self.factory = BrokerFactory()
        self.registry = BrokerRegistry()

    def __call__(self, request):
        current_url = resolve(request.path_info).url_name

        # Skip authentication checks for public URLs
        if self._is_public_url(current_url):
            return self.get_response(request)

        # Check if any brokers are configured first
        if not self._has_configured_brokers():
            # No brokers configured - allow access to login pages for initial setup
            self.logger.info("No brokers configured - allowing access for initial setup")
            return self.get_response(request)

        # Perform basic authentication checks
        should_redirect, redirect_reason, preserve_session = self._check_basic_authentication(request)

        # Redirect to login if authentication failed
        if should_redirect:
            if preserve_session:
                self.logger.warning(f"{LogMessages.REDIRECT_PRESERVING_SESSION}: {redirect_reason}")
            else:
                self.logger.warning(f"{LogMessages.REDIRECT_CLEARING_SESSION}: {redirect_reason}")
                self.auth_service.logout_user(request)
            return redirect("login")

        return self.get_response(request)

    def _check_basic_authentication(self, request) -> tuple[bool, str, bool]:
        """
        Check basic authentication that applies to all brokers.

        Returns:
            tuple: (should_redirect_to_login, redirect_reason, preserve_session)
        """
        # Check if user is authenticated with ANY broker
        if not self._is_authenticated_with_any_broker(request) and not self.auth_service.is_offline_mode():
            return True, AuthenticationErrorMessages.SESSION_NOT_AUTHENTICATED, False

        # Check maintenance mode access
        if not self.auth_service.is_maintenance_mode_allowed() and not self.auth_service.is_offline_mode():
            return False, AuthenticationErrorMessages.MAINTENANCE_MODE_ACCESS_DENIED, False

        return False, "", False

    def _is_authenticated_with_any_broker(self, request) -> bool:
        """
        Check if user is authenticated with any broker.

        This method checks for authentication across all registered brokers,
        including broker-specific session keys.

        Args:
            request: The HTTP request containing session data

        Returns:
            True if authenticated with at least one broker, False otherwise
        """
        try:
            # Check DEGIRO authentication (backward compatibility)
            if self.auth_service.is_user_authenticated(request):
                self.logger.debug("User authenticated with DEGIRO")
                return True

            # Check broker-specific authentication for other brokers
            registered_brokers = self.registry.get_registered_brokers()

            for broker_name in registered_brokers:
                # Skip DEGIRO as it's already checked above
                if broker_name == "degiro":
                    continue

                # Check broker-specific session key
                broker_auth_key = SessionKeys.get_authenticated_key(broker_name)
                if request.session.get(broker_auth_key, False):
                    self.logger.debug(f"User authenticated with {broker_name}")
                    return True

            self.logger.debug("User not authenticated with any broker")
            return False

        except Exception as e:
            self.logger.error(f"Error checking broker authentication: {str(e)}")
            return False

    def _is_public_url(self, url_name: Optional[str]) -> bool:
        """Check if URL is public and doesn't require authentication."""
        return url_name in self.PUBLIC_URLS

    def _has_configured_brokers(self) -> bool:
        """
        Check if any brokers are configured and enabled with valid credentials.

        Returns:
            True if at least one broker is configured, enabled, and has valid credentials
        """
        try:
            from stonks_overwatch.services.utilities.credential_validator import CredentialValidator

            registered_brokers = self.registry.get_registered_brokers()

            for broker_name in registered_brokers:
                try:
                    config = self.factory.create_config(broker_name)
                    if config and config.is_enabled():
                        # Check if broker has valid credentials
                        credentials = config.get_credentials
                        if credentials and CredentialValidator.has_valid_credentials(broker_name, credentials):
                            return True
                except Exception as e:
                    self.logger.warning(f"Error checking broker {broker_name}: {str(e)}")
                    continue

            return False

        except Exception as e:
            self.logger.error(f"Error checking configured brokers: {str(e)}")
            # Default to False to redirect to broker selector when in doubt
            return False
