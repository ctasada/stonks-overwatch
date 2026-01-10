from django.http import HttpRequest, HttpResponse
from django.shortcuts import redirect
from django.views import View

from stonks_overwatch.core.factories.broker_factory import BrokerFactory
from stonks_overwatch.core.factories.broker_registry import BrokerRegistry
from stonks_overwatch.utils.core.logger import StonksLogger
from stonks_overwatch.utils.core.session_keys import SessionKeys


class RootRedirectView(View):
    """
    Root redirect view that intelligently redirects users based on broker configuration.

    - If brokers are configured and enabled: redirect to dashboard
    - If no brokers are configured: redirect to broker selector
    """

    logger = StonksLogger.get_logger("stonks_overwatch.root_redirect", "[VIEW|ROOT_REDIRECT]")

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.factory = BrokerFactory()
        self.registry = BrokerRegistry()

    def get(self, request: HttpRequest) -> HttpResponse:
        """
        Handle GET request and redirect appropriately.

        Args:
            request: The HTTP request

        Returns:
            HttpResponse: Redirect to appropriate page
        """
        try:
            # Check if user is already authenticated and has configured brokers
            if self._has_configured_brokers():
                # Check if user is authenticated for any broker
                if self._is_user_authenticated(request):
                    self.logger.debug("User authenticated with configured brokers - redirecting to dashboard")
                    return redirect("dashboard")
                else:
                    self.logger.debug("User not authenticated but brokers configured - redirecting to login")
                    return redirect("login")
            else:
                self.logger.debug("No brokers configured - redirecting to login (broker selector)")
                return redirect("login")

        except Exception as e:
            self.logger.error(f"Error in root redirect: {str(e)}")
            # Default fallback to login
            return redirect("login")

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
            return False

    def _is_user_authenticated(self, request: HttpRequest) -> bool:
        """
        Check if user is authenticated for any broker.

        Args:
            request: The HTTP request

        Returns:
            True if user is authenticated for any broker
        """
        try:
            # Check session for authentication status for any broker
            broker_sessions = [
                SessionKeys.get_authenticated_key("degiro"),
                SessionKeys.get_authenticated_key("bitvavo"),
                SessionKeys.get_authenticated_key("ibkr"),
            ]

            for session_key in broker_sessions:
                if request.session.get(session_key, False):
                    return True

            # Also check the main authentication service for DEGIRO (backward compatibility)
            try:
                from stonks_overwatch.core.authentication_locator import get_authentication_service

                auth_service = get_authentication_service()
                if auth_service.is_user_authenticated(request):
                    return True
            except Exception as e:
                self.logger.warning(f"Error checking main authentication service: {str(e)}")

            return False

        except Exception as e:
            self.logger.error(f"Error checking user authentication: {str(e)}")
            return False
