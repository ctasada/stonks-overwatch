from django.http import HttpRequest, HttpResponse
from django.shortcuts import redirect
from django.views import View

from stonks_overwatch.core.factories.broker_factory import BrokerFactory
from stonks_overwatch.core.factories.broker_registry import BrokerRegistry
from stonks_overwatch.utils.core.logger import StonksLogger


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
            registered_brokers = self.registry.get_registered_brokers()

            for broker_name in registered_brokers:
                try:
                    config = self.factory.create_config(broker_name)
                    if config and config.is_enabled():
                        # Check if broker has valid credentials
                        credentials = config.get_credentials
                        if credentials and self._has_valid_credentials(broker_name, credentials):
                            return True
                except Exception as e:
                    self.logger.warning(f"Error checking broker {broker_name}: {str(e)}")
                    continue

            return False

        except Exception as e:
            self.logger.error(f"Error checking configured brokers: {str(e)}")
            return False

    def _has_valid_credentials(self, broker_name: str, credentials) -> bool:
        """
        Check if broker credentials are valid (not placeholder values).

        Args:
            broker_name: Name of the broker
            credentials: Broker credentials object

        Returns:
            True if credentials appear to be valid (not placeholders)
        """
        try:
            if broker_name == "degiro":
                return (
                    hasattr(credentials, "username")
                    and hasattr(credentials, "password")
                    and credentials.username
                    and credentials.password
                    and credentials.username != "USERNAME"
                    and credentials.password != "PASSWORD"
                    and len(credentials.username) > 2
                    and len(credentials.password) > 2
                )
            elif broker_name == "bitvavo":
                return (
                    hasattr(credentials, "apikey")
                    and hasattr(credentials, "apisecret")
                    and credentials.apikey
                    and credentials.apisecret
                    and credentials.apikey != "BITVAVO API KEY"
                    and credentials.apisecret != "BITVAVO API SECRET"
                    and len(credentials.apikey) > 10
                    and len(credentials.apisecret) > 10
                )
            elif broker_name == "ibkr":
                return (
                    hasattr(credentials, "access_token")
                    and credentials.access_token
                    and credentials.access_token != "IBKR ACCESS TOKEN"
                    and len(credentials.access_token) > 10
                )
            else:
                # For unknown brokers, assume valid if credentials exist
                return credentials is not None

        except Exception as e:
            self.logger.warning(f"Error validating credentials for {broker_name}: {str(e)}")
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
                "degiro_authenticated",
                "bitvavo_authenticated",
                "ibkr_authenticated",
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
