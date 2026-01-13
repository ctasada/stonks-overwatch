from typing import Optional

from django.contrib import messages
from django.http import HttpRequest, HttpResponse
from django.shortcuts import redirect, render
from django.views import View

from stonks_overwatch.core.factories.broker_factory import BrokerFactory
from stonks_overwatch.core.factories.broker_registry import BrokerRegistry
from stonks_overwatch.jobs.jobs_scheduler import JobsScheduler
from stonks_overwatch.utils.core.constants import AuthenticationErrorMessages
from stonks_overwatch.utils.core.logger import StonksLogger
from stonks_overwatch.utils.core.session_keys import SessionKeys


class BrokerLogin(View):
    """
    View for broker-specific login pages.

    Handles user authentication for different brokers (DEGIRO, Bitvavo, IBKR).
    Supports different authentication flows based on the broker type.
    """

    TEMPLATE_NAME = "broker_login.html"  # Default fallback
    logger = StonksLogger.get_logger("stonks_overwatch.broker_login", "[VIEW|BROKER_LOGIN]")

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.factory = BrokerFactory()
        self.registry = BrokerRegistry()

    def _get_template_name(self, broker_name: str) -> str:
        """Get the template name for the specific broker."""
        template_mapping = {
            "degiro": "login/degiro_login.html",
            "bitvavo": "login/bitvavo_login.html",
            "ibkr": "login/ibkr_login.html",
        }
        return template_mapping.get(broker_name, "login/degiro_login.html")

    def get(self, request: HttpRequest, broker_name: str) -> HttpResponse:
        """
        Display the broker-specific login page.

        Args:
            request: The HTTP request
            broker_name: Name of the broker (degiro, bitvavo, ibkr)

        Returns:
            HttpResponse: Rendered login template or redirect to broker selector
        """
        # Validate broker
        if not self._is_valid_broker(broker_name):
            messages.error(request, f"Broker '{broker_name}' is not supported")
            return redirect("login")

        # Get broker configuration
        config = self.factory.create_config(broker_name)
        if not config:
            messages.error(request, f"Broker '{broker_name}' is not configured")
            return redirect("login")

        # Check authentication state for this broker
        show_otp = self._check_totp_required(request, broker_name)
        show_in_app_auth = self._check_in_app_auth_required(request, broker_name)
        show_loading = self._check_authenticated(request, broker_name)

        context = {
            "broker_name": broker_name,
            "broker_display_name": self._get_display_name(broker_name),
            "broker_logo": f"logos/{broker_name}.svg",
            "show_otp": show_otp,
            "show_loading": show_loading,
            "show_in_app_auth": show_in_app_auth,
            "auth_fields": self._get_auth_fields(broker_name),
        }

        template_name = self._get_template_name(broker_name)
        return render(request, template_name, context=context)

    def post(self, request: HttpRequest, broker_name: str) -> HttpResponse:
        """
        Handle broker-specific login form submission.

        Args:
            request: The HTTP request
            broker_name: Name of the broker

        Returns:
            HttpResponse: Rendered template or redirect
        """
        # Validate broker
        if not self._is_valid_broker(broker_name):
            messages.error(request, f"Broker '{broker_name}' is not supported")
            return redirect("login")

        # Handle portfolio update request
        if request.POST.get("update_portfolio"):
            JobsScheduler.update_portfolio()
            return redirect("dashboard")

        # Handle in-app authentication
        if request.POST.get("in_app_auth"):
            return self._handle_in_app_authentication(request, broker_name)

        # Extract credentials based on broker type
        credentials = self._extract_credentials(request, broker_name)
        if not credentials:
            if broker_name == "ibkr":
                messages.error(
                    request,
                    "OAuth credentials are required (access token, access token secret, consumer key, and DH prime).",
                )
            else:
                messages.error(request, AuthenticationErrorMessages.CREDENTIALS_REQUIRED)
            return self.get(request, broker_name)

        # Perform authentication
        auth_result = self._perform_authentication(request, broker_name, credentials)

        # Handle authentication result
        if auth_result.get("success"):
            self.logger.info(f"Login successful for broker: {broker_name}")

            # Show loading screen for all brokers to allow portfolio initialization
            # This allows the portfolio update to happen before going to dashboard
            return self.get(request, broker_name)
        else:
            # Add error message and re-render form
            messages.error(request, auth_result.get("message", "Authentication failed"))
            return self.get(request, broker_name)

    def _is_valid_broker(self, broker_name: str) -> bool:
        """Check if the broker is registered and supported."""
        return broker_name in self.registry.get_registered_brokers()

    def _get_display_name(self, broker_name: str) -> str:
        """Get the display name for a broker."""
        display_names = {
            "degiro": "DEGIRO",
            "bitvavo": "Bitvavo",
            "ibkr": "Interactive Brokers",
        }
        return display_names.get(broker_name, broker_name.title())

    def _get_auth_fields(self, broker_name: str) -> dict:
        """Get the authentication fields required for each broker."""
        if broker_name == "degiro":
            return {
                "username_label": "Username",
                "password_label": "Password",
                "supports_2fa": True,
                "supports_remember_me": True,
            }
        elif broker_name == "bitvavo":
            return {
                "username_label": "API Key",
                "password_label": "API Secret",
                "supports_2fa": False,
                "supports_remember_me": True,
            }
        elif broker_name == "ibkr":
            return {
                "access_token_label": "Access Token",
                "access_token_secret_label": "Access Token Secret",
                "consumer_key_label": "Consumer Key",
                "dh_prime_label": "DH Prime",
                "encryption_key_label": "Encryption Key (Optional)",
                "signature_key_label": "Signature Key (Optional)",
                "supports_2fa": False,
                "supports_remember_me": True,
                "auth_type": "oauth",  # Indicate this uses OAuth instead of username/password
            }
        else:
            return {
                "username_label": "Username",
                "password_label": "Password",
                "supports_2fa": False,
                "supports_remember_me": False,
            }

    def _check_totp_required(self, request: HttpRequest, broker_name: str) -> bool:
        """Check if TOTP is required for this broker."""
        # For now, only DEGIRO supports TOTP
        if broker_name == "degiro":
            # Check session for TOTP requirement
            return request.session.get(SessionKeys.get_totp_required_key(broker_name), False)
        return False

    def _check_in_app_auth_required(self, request: HttpRequest, broker_name: str) -> bool:
        """Check if in-app authentication is required for this broker."""
        # For now, only DEGIRO supports in-app auth
        if broker_name == "degiro":
            return request.session.get(SessionKeys.get_in_app_auth_required_key(broker_name), False)
        return False

    def _check_authenticated(self, request: HttpRequest, broker_name: str) -> bool:
        """Check if user is authenticated for this broker."""
        # Check session for authentication status
        return request.session.get(SessionKeys.get_authenticated_key(broker_name), False)

    def _extract_credentials(self, request: HttpRequest, broker_name: str) -> Optional[dict]:
        """Extract credentials from request based on broker type."""
        if broker_name == "degiro":
            return self._extract_degiro_credentials(request)
        elif broker_name == "bitvavo":
            return self._extract_bitvavo_credentials(request)
        elif broker_name == "ibkr":
            return self._extract_ibkr_credentials(request)
        return None

    def _extract_degiro_credentials(self, request: HttpRequest) -> Optional[dict]:
        """Extract DEGIRO credentials from request."""
        username = request.POST.get("username")
        password = request.POST.get("password")
        one_time_password = request.POST.get("2fa_code")
        remember_me = request.POST.get("remember_me") == "true"

        # Convert 2FA code to integer if provided
        if one_time_password:
            try:
                one_time_password = int(one_time_password)
            except (ValueError, TypeError):
                one_time_password = None

        # Handle TOTP flow: if only 2FA code is provided, authentication service
        # will retrieve stored credentials from session (stored in correct key)
        if not username and not password and one_time_password:
            return {
                "one_time_password": one_time_password,
            }

        if username and password:
            return {
                "username": username,
                "password": password,
                "one_time_password": one_time_password,
                "remember_me": remember_me,
            }
        return None

    def _extract_bitvavo_credentials(self, request: HttpRequest) -> Optional[dict]:
        """Extract Bitvavo credentials from request."""
        api_key = request.POST.get("username")  # Using username field for API key
        api_secret = request.POST.get("password")  # Using password field for API secret
        remember_me = request.POST.get("remember_me") == "true"

        if api_key and api_secret:
            return {
                "api_key": api_key,
                "api_secret": api_secret,
                "remember_me": remember_me,
            }
        return None

    def _extract_ibkr_credentials(self, request: HttpRequest) -> Optional[dict]:
        """Extract IBKR OAuth credentials from request."""
        access_token = request.POST.get("access_token")
        access_token_secret = request.POST.get("access_token_secret")
        consumer_key = request.POST.get("consumer_key")
        dh_prime = request.POST.get("dh_prime")
        encryption_key = request.POST.get("encryption_key")
        signature_key = request.POST.get("signature_key")
        remember_me = request.POST.get("remember_me") == "true"

        if access_token and access_token_secret and consumer_key and dh_prime:
            return {
                "access_token": access_token,
                "access_token_secret": access_token_secret,
                "consumer_key": consumer_key,
                "dh_prime": dh_prime,
                "encryption_key": encryption_key,
                "signature_key": signature_key,
                "remember_me": remember_me,
            }
        return None

    def _perform_authentication(self, request: HttpRequest, broker_name: str, credentials: dict) -> dict:
        """Perform authentication for the specified broker."""
        try:
            if broker_name == "degiro":
                return self._authenticate_degiro(request, credentials)
            elif broker_name == "bitvavo":
                return self._authenticate_bitvavo(request, credentials)
            elif broker_name == "ibkr":
                return self._authenticate_ibkr(request, credentials)
            else:
                return {"success": False, "message": f"Authentication not implemented for {broker_name}"}
        except Exception as e:
            self.logger.error(f"Authentication error for {broker_name}: {str(e)}")
            return {"success": False, "message": "Authentication failed due to technical error"}

    def _authenticate_degiro(self, request: HttpRequest, credentials: dict) -> dict:
        """Authenticate with DEGIRO."""
        # For now, use the existing authentication service for DEGIRO
        # This is a placeholder - you would integrate with the existing DEGIRO auth service
        try:
            from stonks_overwatch.core.authentication_locator import get_authentication_service

            auth_service = get_authentication_service()

            if credentials.get("one_time_password") and "username" not in credentials:
                # Handle TOTP authentication (2FA code only, credentials in session)
                auth_result = auth_service.handle_totp_authentication(request, credentials["one_time_password"])
            else:
                # Handle initial authentication (username + password, optionally with 2FA)
                auth_result = auth_service.authenticate_user(
                    request=request,
                    username=credentials["username"],
                    password=credentials["password"],
                    one_time_password=credentials.get("one_time_password"),
                    remember_me=credentials.get("remember_me", False),
                )

            if auth_result.is_success:
                # Clear any pending auth flags since authentication succeeded
                request.session[SessionKeys.get_authenticated_key("degiro")] = True
                request.session[SessionKeys.get_totp_required_key("degiro")] = False
                request.session[SessionKeys.get_in_app_auth_required_key("degiro")] = False
                return {"success": True, "message": "Authentication successful"}
            else:
                # Handle different authentication results
                if hasattr(auth_result, "result"):
                    from stonks_overwatch.core.interfaces.authentication_service import AuthenticationResult

                    if auth_result.result == AuthenticationResult.TOTP_REQUIRED:
                        request.session[SessionKeys.get_totp_required_key("degiro")] = True
                        request.session[SessionKeys.get_in_app_auth_required_key("degiro")] = False
                        # Note: credentials are already stored by authentication service in the correct session key
                        return {"success": False, "message": "2FA code required"}
                    elif auth_result.result == AuthenticationResult.IN_APP_AUTHENTICATION_REQUIRED:
                        request.session[SessionKeys.get_in_app_auth_required_key("degiro")] = True
                        request.session[SessionKeys.get_totp_required_key("degiro")] = False
                        return {"success": False, "message": "In-app authentication required"}

                return {"success": False, "message": auth_result.message or "Authentication failed"}

        except Exception as e:
            self.logger.error(f"DEGIRO authentication error: {str(e)}")
            return {"success": False, "message": "Authentication failed"}

    def _authenticate_bitvavo(self, request: HttpRequest, credentials: dict) -> dict:
        """Authenticate with Bitvavo."""
        try:
            # Create Bitvavo authentication service using factory
            auth_service = self.factory.create_authentication_service("bitvavo")
            if not auth_service:
                return {"success": False, "message": "Bitvavo authentication service not available"}

            # Authenticate user
            auth_result = auth_service.authenticate_user(
                request=request,
                api_key=credentials["api_key"],
                api_secret=credentials["api_secret"],
                remember_me=credentials.get("remember_me", False),
            )

            if auth_result["success"]:
                request.session[SessionKeys.get_authenticated_key("bitvavo")] = True
                return {"success": True, "message": "Authentication successful"}
            else:
                return {"success": False, "message": auth_result["message"]}

        except Exception as e:
            self.logger.error(f"Bitvavo authentication error: {str(e)}")
            return {"success": False, "message": "Authentication failed"}

    def _authenticate_ibkr(self, request: HttpRequest, credentials: dict) -> dict:
        """Authenticate with Interactive Brokers."""
        try:
            # Extract credentials
            access_token = credentials.get("access_token", "")
            access_token_secret = credentials.get("access_token_secret", "")
            consumer_key = credentials.get("consumer_key", "")
            dh_prime = credentials.get("dh_prime", "")
            encryption_key = credentials.get("encryption_key")
            signature_key = credentials.get("signature_key")
            remember_me = credentials.get("remember_me", False)

            # Create IBKR authentication service using factory
            auth_service = self.factory.create_authentication_service("ibkr")
            if not auth_service:
                return {"success": False, "message": "IBKR authentication service not available"}

            # Authenticate using the service
            result = auth_service.authenticate_user(
                request=request,
                access_token=access_token,
                access_token_secret=access_token_secret,
                consumer_key=consumer_key,
                dh_prime=dh_prime,
                encryption_key=encryption_key,
                signature_key=signature_key,
                remember_me=remember_me,
            )

            if result["success"]:
                request.session[SessionKeys.get_authenticated_key("ibkr")] = True
                return {"success": True, "message": "Authentication successful"}
            else:
                return {"success": False, "message": result["message"]}

        except Exception as e:
            self.logger.error(f"IBKR authentication error: {str(e)}")
            return {"success": False, "message": "Authentication failed"}

    def _handle_in_app_authentication(self, request: HttpRequest, broker_name: str) -> HttpResponse:
        """Handle in-app authentication for supported brokers."""
        if broker_name == "degiro":
            # Use existing DEGIRO in-app authentication
            try:
                from stonks_overwatch.core.authentication_locator import get_authentication_service

                auth_service = get_authentication_service()
                auth_result = auth_service.handle_in_app_authentication(request)

                if auth_result.is_success:
                    request.session[SessionKeys.get_authenticated_key("degiro")] = True
                    return redirect("dashboard")
                else:
                    messages.error(request, auth_result.message or "In-app authentication failed")

            except Exception as e:
                self.logger.error(f"In-app authentication error: {str(e)}")
                messages.error(request, "In-app authentication failed")
        else:
            messages.error(request, f"In-app authentication not supported for {broker_name}")

        return self.get(request, broker_name)
