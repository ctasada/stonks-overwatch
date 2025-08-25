from django.contrib import messages
from django.shortcuts import redirect, render
from django.views import View

from stonks_overwatch.core.authentication_locator import get_authentication_service
from stonks_overwatch.core.interfaces.authentication_service import AuthenticationResult
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

    def get(self, request):
        # Use AuthenticationService to check TOTP requirement, in-app auth requirement, and authentication status
        show_otp = self.auth_service.session_manager.is_totp_required(request)
        show_in_app_auth = self.auth_service.session_manager.is_in_app_auth_required(request)
        show_loading = False

        if self.auth_service.is_user_authenticated(request):
            self.logger.info(LogMessages.USER_ALREADY_AUTHENTICATED)
            show_loading = True

        context = {"show_otp": show_otp, "show_loading": show_loading, "show_in_app_auth": show_in_app_auth}
        return render(request, self.TEMPLATE_NAME, context=context, status=200)

    def post(self, request):
        update_portfolio = request.POST.get("update_portfolio") or False
        if update_portfolio:
            # Update portfolio data before loading the dashboard
            JobsScheduler.update_portfolio()
            return redirect("dashboard")

        in_app_auth = request.POST.get("in_app_auth") or False
        if in_app_auth:
            # For in-app authentication, wait until the user is authenticated using DEGIRO app
            # FIXME: Implement waiting code
            return redirect("dashboard")

        # Extract and validate credentials
        credentials = self._extract_credentials(request)
        if not credentials:
            return self._render_login_error(request, AuthenticationErrorMessages.CREDENTIALS_REQUIRED)

        # Perform authentication
        auth_result = self._perform_authentication(request, credentials)

        # Handle result and render response
        show_otp, show_loading, show_in_app_auth = self._handle_auth_result(request, auth_result)

        context = {"show_otp": show_otp, "show_loading": show_loading, "show_in_app_auth": show_in_app_auth}
        return render(request, self.TEMPLATE_NAME, context=context, status=200)

    def _extract_credentials(self, request):
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

    def _perform_authentication(self, request, credentials):
        """Perform authentication using AuthenticationService."""
        if credentials["one_time_password"]:
            return self.auth_service.handle_totp_authentication(request, credentials["one_time_password"])
        else:
            return self.auth_service.authenticate_user(
                request,
                credentials["username"],
                credentials["password"],
                credentials["one_time_password"],
                credentials["remember_me"],
            )

    def _handle_auth_result(self, request, auth_result):
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

    def _render_login_error(self, request, error_message):
        """Render login page with error message."""
        messages.error(request, error_message)
        return render(request, self.TEMPLATE_NAME, context={"show_otp": False, "show_in_app_auth": False}, status=400)
