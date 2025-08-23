from typing import Optional

from django.shortcuts import redirect
from django.urls import resolve

from stonks_overwatch.core.authentication_locator import get_authentication_service
from stonks_overwatch.core.interfaces.authentication_service import AuthenticationResult
from stonks_overwatch.utils.core.constants import AuthenticationErrorMessages, LogMessages
from stonks_overwatch.utils.core.logger import StonksLogger


class DeGiroAuthMiddleware:
    PUBLIC_URLS = {"login", "expired"}

    logger = StonksLogger.get_logger("stonks_overwatch.degiro_auth", "[DEGIRO|AUTH_MIDDLEWARE]")

    def __init__(self, get_response):
        self.get_response = get_response
        # Use optimized service locator for authentication service
        self.auth_service = get_authentication_service()

    def __call__(self, request):
        current_url = resolve(request.path_info).url_name

        # Skip authentication checks for public URLs
        if self._is_public_url(current_url):
            return self.get_response(request)

        # Perform authentication checks
        should_redirect, redirect_reason, preserve_session = self._check_authentication(request)

        # Redirect to login if authentication failed
        if should_redirect:
            if preserve_session:
                self.logger.warning(f"{LogMessages.REDIRECT_PRESERVING_SESSION}: {redirect_reason}")
            else:
                self.logger.warning(f"{LogMessages.REDIRECT_CLEARING_SESSION}: {redirect_reason}")
                self.auth_service.logout_user(request)
            return redirect("login")

        return self.get_response(request)

    def _check_authentication(self, request) -> tuple[bool, str, bool]:
        """
        Check if user authentication is valid.

        Returns:
            tuple: (should_redirect_to_login, redirect_reason, preserve_session)
        """
        # Check DeGiro connection if needed
        connection_redirect, connection_reason, preserve_session = self._check_degiro_connection(request)
        if connection_redirect:
            return True, connection_reason, preserve_session

        # Check basic session authentication
        if not self.auth_service.is_user_authenticated(request) and not self.auth_service.is_offline_mode():
            return True, AuthenticationErrorMessages.SESSION_NOT_AUTHENTICATED, False

        # Check maintenance mode access
        if not self.auth_service.is_maintenance_mode_allowed() and not self.auth_service.is_offline_mode():
            return False, AuthenticationErrorMessages.MAINTENANCE_MODE_ACCESS_DENIED, False

        return False, "", False

    def _check_degiro_connection(self, request) -> tuple[bool, str, bool]:
        """
        Check DeGiro connection status.

        Returns:
            tuple: (should_redirect_to_login, redirect_reason, preserve_session)
        """
        try:
            is_degiro_enabled = self.auth_service.is_degiro_enabled()
            is_degiro_offline = self.auth_service.is_offline_mode()

            self.logger.debug(f"DeGiro Enabled: {is_degiro_enabled}, Offline Mode: {is_degiro_offline}")

            if not is_degiro_enabled or is_degiro_offline:
                return False, "", False

            if not self.auth_service.should_check_connection(request):
                return False, "", False

            # Check DeGiro connection
            connection_result = self.auth_service.check_degiro_connection(request)
            return self._handle_connection_result(request, connection_result)

        except Exception as e:
            self.logger.error(f"{LogMessages.DEGIRO_STATUS_CHECK_FAILED}: {e}", exc_info=True)
            return False, "", False

    def _handle_connection_result(self, request, connection_result) -> tuple[bool, str, bool]:
        """
        Handle the result of DeGiro connection check.

        Args:
            request: The HTTP request
            connection_result: The result from auth_service.check_degiro_connection()

        Returns:
            tuple: (should_redirect_to_login, redirect_reason, preserve_session)
        """
        if connection_result.result == AuthenticationResult.TOTP_REQUIRED:
            # TOTP required means credentials are valid, just need 2FA
            # Set session flag so login page shows 2FA form directly
            self.auth_service.session_manager.set_totp_required(request, True)
            self.logger.info(LogMessages.TOTP_REQUIRED_PRESERVING)
            return True, AuthenticationErrorMessages.TOTP_AUTHENTICATION_REQUIRED, True
        elif connection_result.result in [
            AuthenticationResult.CONNECTION_ERROR,
            AuthenticationResult.CONFIGURATION_ERROR,
            AuthenticationResult.INVALID_CREDENTIALS,
            AuthenticationResult.MAINTENANCE_MODE,
        ]:
            # Authentication failures - clear session and start over
            return (
                True,
                f"{AuthenticationErrorMessages.AUTHENTICATION_FAILED_PREFIX}: {connection_result.message}",
                False,
            )
        elif connection_result.result != AuthenticationResult.SUCCESS:
            # Any other non-success result - clear session
            return True, f"{AuthenticationErrorMessages.AUTHENTICATION_ISSUE_PREFIX}: {connection_result.result}", False

        # Success - no redirect needed
        return False, "", False

    def _is_public_url(self, url_name: Optional[str]) -> bool:
        return url_name in self.PUBLIC_URLS
