from typing import Any

from django.contrib import messages
from django.http import HttpRequest, HttpResponse
from django.shortcuts import redirect, render
from django.views import View

from stonks_overwatch.core.authentication_locator import get_authentication_service
from stonks_overwatch.core.interfaces.authentication_service import AuthenticationResponse, AuthenticationResult
from stonks_overwatch.jobs.jobs_scheduler import JobsScheduler
from stonks_overwatch.utils.core.constants import AuthenticationErrorMessages, LogMessages
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
        # Use optimized service locator for authentication service
        self.auth_service = get_authentication_service()

    def _render_login_template(
        self,
        request: HttpRequest,
        show_otp: bool = False,
        show_loading: bool = False,
        show_in_app_auth: bool = False,
        status: int = 200,
    ) -> HttpResponse:
        """Centralized method to render the login template with appropriate context."""
        context = {"show_otp": show_otp, "show_loading": show_loading, "show_in_app_auth": show_in_app_auth}
        return render(request, self.TEMPLATE_NAME, context=context, status=status)

    def get(self, request: HttpRequest) -> HttpResponse:
        # Use AuthenticationService to check TOTP requirement, in-app auth requirement, and authentication status
        show_otp = False
        show_in_app_auth = False
        show_loading = False

        # If user is already authenticated, show loading screen and skip TOTP/in-app auth checks
        if self.auth_service.is_user_authenticated(request):
            self.logger.info(LogMessages.USER_ALREADY_AUTHENTICATED)
            show_loading = True
        else:
            # Only check for TOTP/in-app auth requirements if user is not authenticated
            show_otp = self.auth_service.session_manager.is_totp_required(request)
            show_in_app_auth = self.auth_service.session_manager.is_in_app_auth_required(request)

        return self._render_login_template(request, show_otp, show_loading, show_in_app_auth)

    def post(self, request: HttpRequest) -> HttpResponse:
        update_portfolio = request.POST.get("update_portfolio") or False
        if update_portfolio:
            # Update portfolio data before loading the dashboard
            JobsScheduler.update_portfolio()
            return redirect("dashboard")

        in_app_auth = request.POST.get("in_app_auth") or False
        if in_app_auth:
            # For in-app authentication, wait until the user is authenticated using DEGIRO app
            return self._handle_in_app_authentication(request)

        # Extract and validate credentials
        credentials = self._extract_credentials(request)
        if not credentials:
            messages.error(request, AuthenticationErrorMessages.CREDENTIALS_REQUIRED)
            return self._render_login_template(request, status=400)

        # Perform authentication
        auth_result = self._perform_authentication(request, credentials)

        # Handle result and render response
        show_otp, show_loading, show_in_app_auth = self._handle_auth_result(request, auth_result)

        return self._render_login_template(request, show_otp, show_loading, show_in_app_auth)

    def _extract_credentials(self, request: HttpRequest) -> dict[str, Any]:
        """Extract and validate credentials from the request."""
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

        # Handle TOTP flow: if only 2FA code is provided, get credentials from session
        if not username and not password and one_time_password:
            # During TOTP flow, credentials should be in session
            session_credentials = self.auth_service.session_manager.get_credentials(request)
            if session_credentials:
                username = session_credentials.username
                password = session_credentials.password
                remember_me = session_credentials.remember_me if session_credentials.remember_me is not None else False

        # Return credentials if we have username and password (either from POST or session)
        if username and password:
            return {
                "username": username,
                "password": password,
                "one_time_password": one_time_password,
                "remember_me": remember_me,
            }

        return None

    def _perform_authentication(self, request: HttpRequest, credentials: dict[str, Any]) -> AuthenticationResponse:
        """Perform authentication using AuthenticationService."""
        if credentials["one_time_password"]:
            return self.auth_service.handle_totp_authentication(request, credentials["one_time_password"])
        else:
            return self.auth_service.authenticate_user(
                request=request,
                username=credentials["username"],
                password=credentials["password"],
                one_time_password=credentials["one_time_password"],
                remember_me=credentials["remember_me"],
            )

    def _handle_auth_result(self, request: HttpRequest, auth_result: AuthenticationResponse):
        """Handle authentication result and set UI state."""
        show_otp = False
        show_loading = False
        show_in_app_auth = False

        if auth_result.is_success:
            self.logger.info(LogMessages.LOGIN_SUCCESSFUL)
            show_loading = True
        elif auth_result.result == AuthenticationResult.TOTP_REQUIRED:
            self.logger.info(LogMessages.TOTP_REQUIRED_USER)
            show_otp = True
        elif auth_result.result == AuthenticationResult.IN_APP_AUTHENTICATION_REQUIRED:
            self.logger.info(LogMessages.IN_APP_AUTH_REQUIRED_USER)
            show_in_app_auth = True
        elif auth_result.result == AuthenticationResult.ACCOUNT_BLOCKED:
            self.logger.warning(LogMessages.ACCOUNT_BLOCKED_USER)
            messages.error(request, AuthenticationErrorMessages.ACCOUNT_BLOCKED)
        elif auth_result.result == AuthenticationResult.INVALID_CREDENTIALS:
            messages.error(request, auth_result.message or AuthenticationErrorMessages.INVALID_CREDENTIALS)
        elif auth_result.result == AuthenticationResult.MAINTENANCE_MODE:
            messages.error(request, auth_result.message or AuthenticationErrorMessages.MAINTENANCE_MODE)
        elif auth_result.result == AuthenticationResult.CONNECTION_ERROR:
            self.logger.error(f"Connection error: {auth_result.message}")
            messages.error(request, AuthenticationErrorMessages.CONNECTION_ERROR)
        else:
            self.logger.error(f"Authentication failed: {auth_result.message}")
            messages.error(request, auth_result.message or AuthenticationErrorMessages.UNEXPECTED_ERROR)

        return show_otp, show_loading, show_in_app_auth

    def _handle_in_app_authentication(self, request: HttpRequest) -> HttpResponse:
        """Handle in-app authentication by delegating to the authentication service."""
        # Use the authentication service to handle in-app authentication
        auth_result = self.auth_service.handle_in_app_authentication(request)

        if auth_result.is_success:
            self.logger.info(LogMessages.LOGIN_SUCCESSFUL)
            return self._render_login_template(request, show_loading=True)
        else:
            # Handle errors from authentication service
            self.logger.error(f"In-app authentication failed: {auth_result.message}")
            if auth_result.result == AuthenticationResult.CONFIGURATION_ERROR:
                messages.error(request, AuthenticationErrorMessages.CONFIGURATION_ERROR)
            elif auth_result.result == AuthenticationResult.CONNECTION_ERROR:
                messages.error(request, AuthenticationErrorMessages.CONNECTION_ERROR)
            else:
                messages.error(request, auth_result.message or AuthenticationErrorMessages.UNEXPECTED_ERROR)

            return self._render_login_template(request, show_in_app_auth=False, status=400)
