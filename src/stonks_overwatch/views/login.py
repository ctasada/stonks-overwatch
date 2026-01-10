from typing import Optional

from django.http import HttpRequest, HttpResponse
from django.shortcuts import redirect, render
from django.views import View

from stonks_overwatch.core.factories.broker_factory import BrokerFactory
from stonks_overwatch.core.factories.broker_registry import BrokerRegistry
from stonks_overwatch.utils.core.logger import StonksLogger


class Login(View):
    """
    View for the login page.
    Handles user authentication and connection to DeGiro.

    The view has 4 states:
    * Initial state: The user is prompted to enter their username and password.
    * TOTP required: The user is prompted to enter their 2FA code.
    * In-app authentication required: The user is prompted to complete authentication in their mobile app.
    * Loading: The user is shown a loading indicator while the portfolio is updated.
    """

    TEMPLATE_NAME = "login.html"
    logger = StonksLogger.get_logger("stonks_overwatch.login", "[VIEW|LOGIN]")

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
                # Auto-auth failed, redirect to broker-specific login page
                self.logger.info(f"Auto-authentication failed for {broker_to_auto_auth}, showing login page")
                return redirect("broker_login", broker_name=broker_to_auto_auth)

        # No stored credentials found, show broker selector
        return self._render_broker_selector(request)

    def post(self, request: HttpRequest) -> HttpResponse:
        # The login page only shows broker selector, so POST requests should redirect to broker-specific login
        # This is a fallback in case someone tries to POST to /login directly
        return redirect("login")

    def _get_available_brokers(self) -> list:
        """
        Get list of available brokers with their metadata.

        Returns:
            List of broker dictionaries with name, display_name, description, and enabled status
        """
        brokers = []

        # Get all registered brokers from the registry
        registered_brokers = self.registry.get_registered_brokers()

        for broker_name in registered_brokers:
            try:
                # Get broker configuration to check if it's enabled
                config = self.factory.create_config(broker_name)

                broker_info = {
                    "name": broker_name,
                    "display_name": self._get_display_name(broker_name),
                    "description": self._get_broker_description(broker_name),
                    "enabled": config.is_enabled() if config else False,
                }

                brokers.append(broker_info)

            except Exception as e:
                self.logger.warning(f"Error getting info for broker {broker_name}: {str(e)}")
                # Still add the broker but mark as not enabled
                brokers.append(
                    {
                        "name": broker_name,
                        "display_name": self._get_display_name(broker_name),
                        "description": "Configuration error",
                        "enabled": False,
                    }
                )

        # Sort brokers: enabled first, then alphabetically
        brokers.sort(key=lambda x: (not x["enabled"], x["display_name"]))

        return brokers

    def _get_display_name(self, broker_name: str) -> str:
        """Get the display name for a broker."""
        display_names = {
            "degiro": "DEGIRO",
            "bitvavo": "Bitvavo",
            "ibkr": "Interactive Brokers",
        }
        return display_names.get(broker_name, broker_name.title())

    def _get_broker_description(self, broker_name: str) -> str:
        """Get a description for a broker."""
        descriptions = {
            "degiro": "European online broker with low fees",
            "bitvavo": "Dutch cryptocurrency exchange platform",
            "ibkr": "Global investment platform with advanced tools",
        }
        return descriptions.get(broker_name, "Investment platform")

    def _get_broker_with_stored_credentials(self) -> Optional[str]:
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

    def _attempt_auto_authentication(self, request: HttpRequest, broker_name: str) -> dict:
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

            # Perform authentication based on broker type
            if broker_name == "degiro":
                return self._auto_authenticate_degiro(request, credentials)
            elif broker_name == "bitvavo":
                return self._auto_authenticate_bitvavo(request, credentials)
            elif broker_name == "ibkr":
                return self._auto_authenticate_ibkr(request, credentials)
            else:
                return {"success": False, "message": f"Auto-authentication not supported for {broker_name}"}

        except Exception as e:
            self.logger.error(f"Error during auto-authentication for {broker_name}: {str(e)}")
            return {"success": False, "message": f"Auto-authentication failed: {str(e)}"}

    def _auto_authenticate_degiro(self, request: HttpRequest, credentials) -> dict:
        """Auto-authenticate with DEGIRO stored credentials."""
        try:
            from stonks_overwatch.core.authentication_locator import get_authentication_service

            auth_service = get_authentication_service()

            # Authenticate with stored credentials
            auth_result = auth_service.authenticate_user(
                request=request,
                username=credentials.username,
                password=credentials.password,
                one_time_password=None,
                remember_me=False,
            )

            if auth_result.is_success:
                request.session["degiro_authenticated"] = True
                return {"success": True, "message": "Auto-authentication successful"}
            else:
                return {"success": False, "message": auth_result.message or "Authentication failed"}

        except Exception as e:
            self.logger.error(f"DEGIRO auto-authentication error: {str(e)}")
            return {"success": False, "message": "Auto-authentication failed"}

    def _auto_authenticate_bitvavo(self, request: HttpRequest, credentials) -> dict:
        """Auto-authenticate with Bitvavo stored credentials."""
        try:
            from stonks_overwatch.services.brokers.bitvavo.services.authentication_service import (
                BitvavoAuthenticationService,
            )

            # Create Bitvavo authentication service with proper config
            config = self.factory.create_config("bitvavo")
            auth_service = BitvavoAuthenticationService(config=config)

            # Authenticate with stored credentials
            auth_result = auth_service.authenticate_user(
                request=request,
                api_key=credentials.apikey,
                api_secret=credentials.apisecret,
                remember_me=False,
            )

            if auth_result["success"]:
                request.session["bitvavo_authenticated"] = True
                return {"success": True, "message": "Auto-authentication successful"}
            else:
                return {"success": False, "message": auth_result["message"]}

        except Exception as e:
            self.logger.error(f"Bitvavo auto-authentication error: {str(e)}")
            return {"success": False, "message": "Auto-authentication failed"}

    def _auto_authenticate_ibkr(self, request: HttpRequest, credentials) -> dict:
        """Auto-authenticate with IBKR stored credentials."""
        # Placeholder for IBKR auto-authentication
        try:
            # TODO: Implement actual IBKR auto-authentication
            # For now, just validate that credentials exist
            if hasattr(credentials, "access_token") and credentials.access_token:
                request.session["ibkr_authenticated"] = True
                return {"success": True, "message": "Auto-authentication successful"}
            else:
                return {"success": False, "message": "Invalid credentials"}

        except Exception as e:
            self.logger.error(f"IBKR auto-authentication error: {str(e)}")
            return {"success": False, "message": "Auto-authentication failed"}
