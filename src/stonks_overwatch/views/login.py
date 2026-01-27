from typing import Optional

from django.http import HttpRequest, HttpResponse
from django.shortcuts import redirect, render
from django.views import View

from stonks_overwatch.constants.brokers import BrokerName
from stonks_overwatch.core.factories.broker_factory import BrokerFactory
from stonks_overwatch.core.factories.broker_registry import BrokerRegistry
from stonks_overwatch.services.models import PortfolioId
from stonks_overwatch.utils.core.logger import StonksLogger
from stonks_overwatch.utils.core.session_keys import SessionKeys


class BrokerAuthStrategy:
    """
    Strategy pattern for broker-specific authentication logic.

    This class encapsulates broker-specific authentication configuration,
    reducing code duplication in the Login view.
    """

    def __init__(
        self,
        broker_name: BrokerName,
        use_factory: bool = True,
        handles_totp: bool = False,
    ):
        """
        Initialize authentication strategy for a broker.

        Args:
            broker_name: The broker name
            use_factory: Whether to use BrokerFactory (False for DEGIRO which uses locator)
            handles_totp: Whether this broker supports TOTP/2FA
        """
        self.broker_name = broker_name
        self.use_factory = use_factory
        self.handles_totp = handles_totp


class Login(View):
    """
    View for the login page.
    Handles user authentication and connection to brokers.

    The view has 4 states:
    * Initial state: The user is prompted to select a broker.
    * TOTP required: The user is prompted to enter their 2FA code.
    * In-app authentication required: The user is prompted to complete authentication in their mobile app.
    * Loading: The user is shown a loading indicator while the portfolio is updated.
    """

    TEMPLATE_NAME = "login.html"
    logger = StonksLogger.get_logger("stonks_overwatch.login", "[VIEW|LOGIN]")

    # Configuration for broker-specific authentication strategies
    BROKER_AUTH_STRATEGIES = {
        BrokerName.DEGIRO: BrokerAuthStrategy(
            broker_name=BrokerName.DEGIRO,
            use_factory=False,
            handles_totp=True,
        ),
        BrokerName.BITVAVO: BrokerAuthStrategy(
            broker_name=BrokerName.BITVAVO,
            use_factory=True,
            handles_totp=False,
        ),
        BrokerName.IBKR: BrokerAuthStrategy(
            broker_name=BrokerName.IBKR,
            use_factory=True,
            handles_totp=False,
        ),
    }

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.factory = BrokerFactory()
        self.registry = BrokerRegistry()

    def _render_broker_selector(self, request: HttpRequest) -> HttpResponse:
        """Render the broker selector."""
        try:
            available_brokers = self._get_available_brokers()

            context = {
                "available_brokers": available_brokers,
            }

            self.logger.info(f"Displaying broker selector with {len(available_brokers)} brokers")
            return render(request, self.TEMPLATE_NAME, context=context)

        except Exception as e:
            self.logger.error(f"Error displaying broker selector: {str(e)}")
            context = {"available_brokers": []}
            return render(request, self.TEMPLATE_NAME, context=context, status=500)

    def get(self, request: HttpRequest) -> HttpResponse:
        # Check if we should attempt auto-authentication
        broker_to_auto_auth = self._get_broker_with_stored_credentials()

        if broker_to_auto_auth:
            # Try to auto-authenticate
            auth_result = self._attempt_auto_authentication(request, broker_to_auto_auth)

            if auth_result.get("success"):
                self.logger.info(f"Auto-authentication successful for {broker_to_auto_auth}")
                return redirect("dashboard")
            else:
                # Auto-auth failed - check if it's due to TOTP/2FA requirement
                if auth_result.get("requires_totp") or auth_result.get("requires_in_app_auth"):
                    # TOTP or in-app auth required - redirect to broker-specific login page
                    self.logger.info(
                        f"Auto-authentication requires 2FA for {broker_to_auto_auth}, redirecting to broker login"
                    )
                    return redirect("broker_login", broker_name_str=broker_to_auto_auth)
                else:
                    # Other authentication failure - show broker selector so user can choose
                    self.logger.info(
                        f"Auto-authentication failed for {broker_to_auto_auth}: {auth_result.get('message')}"
                    )
                    self.logger.info("Showing broker selector for manual selection")

        # No stored credentials found or auto-auth failed (non-2FA), show broker selector
        return self._render_broker_selector(request)

    def post(self, request: HttpRequest) -> HttpResponse:
        # The login page only shows broker selector, so POST requests should redirect to broker-specific login
        # This is a fallback in case someone tries to POST to /login directly
        return redirect("login")

    def _get_available_brokers(self) -> list:
        """
        Get list of available brokers with their metadata.

        Returns:
            List of broker dictionaries with name, display_name, description, enabled status, and stable flag
        """
        brokers = []

        # Get all registered brokers from the registry (returns BrokerName enums)
        registered_brokers = self.registry.get_registered_brokers()

        for broker_enum in registered_brokers:
            try:
                # Get broker configuration to check if it's enabled
                config = self.factory.create_config(broker_enum)

                # Get PortfolioId to check stability
                portfolio_id = PortfolioId.from_broker_name(broker_enum)

                broker_info = {
                    "name": broker_enum.value,  # Convert enum to string for template
                    "display_name": broker_enum.display_name,
                    "description": self._get_broker_description(broker_enum),
                    "enabled": config.is_enabled() if config else False,
                    "stable": portfolio_id.stable,  # Use PortfolioId.stable for experimental badge
                }

                brokers.append(broker_info)

            except Exception as e:
                self.logger.warning(f"Error getting info for broker {broker_enum}: {str(e)}")
                # Still add the broker but mark as not enabled and not stable
                brokers.append(
                    {
                        "name": broker_enum.value,  # Convert enum to string for template
                        "display_name": broker_enum.display_name,
                        "description": "Configuration error",
                        "enabled": False,
                        "stable": False,
                    }
                )

        # Sort brokers alphabetically
        brokers.sort(key=lambda x: x["display_name"])

        return brokers

    def _get_broker_description(self, broker_name: BrokerName) -> str:
        """Get a description for a broker."""
        descriptions = {
            BrokerName.DEGIRO: "European online broker with low fees",
            BrokerName.BITVAVO: "Dutch cryptocurrency exchange platform",
            BrokerName.IBKR: "Global investment platform with advanced tools",
        }
        return descriptions.get(broker_name, "Investment platform")

    def _get_broker_with_stored_credentials(self) -> Optional[BrokerName]:
        """
        Find a broker with stored credentials for auto-authentication.

        Returns:
            Broker name if found, None otherwise
        """
        try:
            from stonks_overwatch.services.utilities.credential_validator import CredentialValidator

            available_brokers = self._get_available_brokers()

            # Only attempt auto-auth for enabled brokers
            enabled_brokers = [b for b in available_brokers if b["enabled"]]

            for broker_info in enabled_brokers:
                broker_name = broker_info["name"]
                config = self.factory.create_config(broker_name)

                if config and config.is_enabled():
                    credentials = config.get_credentials

                    # Check if credentials are valid (not placeholders)
                    if credentials and CredentialValidator.has_valid_credentials(broker_name, credentials):
                        self.logger.debug(f"Found stored credentials for broker: {broker_name}")
                        return broker_name

            return None

        except Exception as e:
            self.logger.error(f"Error checking for stored credentials: {str(e)}")
            return None

    def _attempt_auto_authentication(self, request: HttpRequest, broker_name: BrokerName) -> dict:
        """
        Attempt automatic authentication with stored credentials.

        Args:
            request: The HTTP request
            broker_name: Name of the broker to authenticate with

        Returns:
            Dictionary with success status and message
        """
        try:
            self.logger.info(f"Attempting auto-authentication for broker: {broker_name}")

            # Get broker configuration
            config = self.factory.create_config(broker_name)
            if not config:
                return {"success": False, "message": f"Broker {broker_name} not configured"}

            credentials = config.get_credentials
            if not credentials:
                return {"success": False, "message": "No credentials found"}

            # Get authentication strategy for this broker
            strategy = self.BROKER_AUTH_STRATEGIES.get(broker_name)
            if not strategy:
                return {"success": False, "message": f"Auto-authentication not supported for {broker_name}"}

            # Use generic authentication method with strategy
            return self._auto_authenticate_with_strategy(request, strategy, credentials)

        except Exception as e:
            self.logger.error(f"Error during auto-authentication for {broker_name}: {str(e)}")
            return {"success": False, "message": f"Auto-authentication failed: {str(e)}"}

    def _auto_authenticate_with_strategy(self, request: HttpRequest, strategy: BrokerAuthStrategy, credentials) -> dict:
        """
        Generic auto-authentication method using strategy pattern.

        Args:
            request: The HTTP request
            strategy: The broker-specific authentication strategy
            credentials: The stored credentials object

        Returns:
            Dictionary with success status and message
        """
        try:
            broker_name = strategy.broker_name

            # Get authentication service based on strategy
            if strategy.use_factory:
                auth_service = self.factory.create_authentication_service(broker_name)
                if not auth_service:
                    return {"success": False, "message": f"{broker_name} authentication service not available"}
            else:
                # Special case for DEGIRO which uses authentication locator
                from stonks_overwatch.core.authentication_locator import get_authentication_service

                auth_service = get_authentication_service()

            # Check if already authenticated (IBKR optimization)
            if broker_name == BrokerName.IBKR and auth_service.is_user_authenticated(request):
                return {"success": True, "message": "Already authenticated"}

            # Extract credentials using credential's to_auth_params method
            auth_params = credentials.to_auth_params()

            # Validate required credentials for IBKR
            if broker_name == BrokerName.IBKR:
                required_fields = ["access_token", "access_token_secret", "consumer_key", "dh_prime"]
                if not all(auth_params.get(field) for field in required_fields):
                    return {"success": False, "message": "Missing required OAuth credentials"}

            # Authenticate with broker-specific parameters
            auth_result = auth_service.authenticate_user(request=request, **auth_params)

            # Handle response based on broker type
            return self._process_auth_result(request, broker_name, auth_result, strategy.handles_totp)

        except Exception as e:
            self.logger.error(f"{strategy.broker_name} auto-authentication error: {str(e)}")
            return {"success": False, "message": "Auto-authentication failed"}

    def _process_auth_result(
        self, request: HttpRequest, broker_name: BrokerName, auth_result, handles_totp: bool
    ) -> dict:
        """
        Process authentication result and convert to standard format.

        Args:
            request: The HTTP request
            broker_name: The broker name
            auth_result: Authentication result (AuthenticationResponse or dict)
            handles_totp: Whether this broker supports TOTP

        Returns:
            Standardized dictionary with success status and message
        """
        # DEGIRO returns AuthenticationResponse object, others return dict
        if hasattr(auth_result, "is_success"):
            # AuthenticationResponse object (DEGIRO)
            from stonks_overwatch.core.interfaces.authentication_service import AuthenticationResult

            if auth_result.is_success:
                request.session[SessionKeys.get_authenticated_key(broker_name)] = True
                return {"success": True, "message": "Auto-authentication successful"}
            elif handles_totp and auth_result.result == AuthenticationResult.TOTP_REQUIRED:
                return {"success": False, "message": "TOTP authentication required", "requires_totp": True}
            elif handles_totp and auth_result.result == AuthenticationResult.IN_APP_AUTHENTICATION_REQUIRED:
                return {"success": False, "message": "In-app authentication required", "requires_in_app_auth": True}
            else:
                return {"success": False, "message": auth_result.message or "Authentication failed"}
        else:
            # Dict response (Bitvavo, IBKR, MetaTrader4)
            if auth_result.get("success"):
                request.session[SessionKeys.get_authenticated_key(broker_name)] = True
                return {"success": True, "message": "Auto-authentication successful"}
            else:
                return {"success": False, "message": auth_result.get("message", "Authentication failed")}
