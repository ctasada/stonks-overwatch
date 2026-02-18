"""
DEGIRO-specific authentication middleware.

This middleware handles authentication logic that is specific to DEGIRO,
such as connection checking, TOTP handling, and in-app authentication.
"""

from django.shortcuts import redirect

from stonks_overwatch.core.authentication_locator import get_authentication_service
from stonks_overwatch.core.interfaces.authentication_service import AuthenticationResult
from stonks_overwatch.utils.core.constants import AuthenticationErrorMessages, LogMessages
from stonks_overwatch.utils.core.logger import StonksLogger


class DeGiroAuthMiddleware:
    """
    DEGIRO-specific authentication middleware.

    Handles:
    - DEGIRO connection status checking
    - TOTP (2FA) flow management
    - In-app authentication flow
    - DEGIRO-specific session management

    Note: This middleware should run AFTER the general AuthenticationMiddleware.
    """

    logger = StonksLogger.get_logger("stonks_overwatch.degiro_auth", "[DEGIRO|AUTH_MIDDLEWARE]")

    def __init__(self, get_response):
        self.get_response = get_response
        self.auth_service = get_authentication_service()

    def __call__(self, request):
        # Only perform DEGIRO-specific checks if DEGIRO is enabled
        if not self._should_check_degiro(request):
            return self.get_response(request)

        # Check DEGIRO connection if needed
        should_redirect, redirect_reason, preserve_session = self._check_degiro_connection(request)

        # Redirect to login if DEGIRO authentication failed
        if should_redirect:
            if preserve_session:
                self.logger.warning(f"{LogMessages.REDIRECT_PRESERVING_SESSION}: {redirect_reason}")
            else:
                self.logger.warning(f"{LogMessages.REDIRECT_CLEARING_SESSION}: {redirect_reason}")
                self.auth_service.logout_user(request)
            return redirect("login")

        return self.get_response(request)

    def _should_check_degiro(self, request) -> bool:
        """
        Determine if DEGIRO-specific checks should be performed.

        Returns:
            True if DEGIRO checks should be performed
        """
        try:
            # Skip if DEGIRO is not enabled or in offline mode
            if not self.auth_service.is_broker_enabled() or self.auth_service.is_offline_mode():
                return False

            # Skip if connection check is not needed
            if not self.auth_service.should_check_connection(request):
                return False

            return True

        except Exception as e:
            self.logger.error(f"Error determining if DEGIRO check is needed: {e}")
            return False

    def _check_degiro_connection(self, request) -> tuple[bool, str, bool]:
        """
        Check DeGiro connection status.

        Returns:
            tuple: (should_redirect_to_login, redirect_reason, preserve_session)
        """
        try:
            self.logger.debug("Checking DEGIRO connection status")

            # Check DeGiro connection
            connection_result = self.auth_service.check_broker_connection(request)
            return self._handle_connection_result(request, connection_result)

        except Exception as e:
            self.logger.error(f"{LogMessages.DEGIRO_STATUS_CHECK_FAILED}: {e}", exc_info=True)
            return False, "", False

    def _handle_connection_result(self, request, connection_result) -> tuple[bool, str, bool]:
        """
        Handle the result of DeGiro connection check.

        Args:
            request: The HTTP request
            connection_result: The result from auth_service.check_broker_connection()

        Returns:
            tuple: (should_redirect_to_login, redirect_reason, preserve_session)
        """
        if connection_result.result == AuthenticationResult.TOTP_REQUIRED:
            # TOTP required means credentials are valid, just need 2FA
            # Set session flag so login page shows 2FA form directly
            self.auth_service.session_manager.set_totp_required(request, True)
            self.logger.info(LogMessages.TOTP_REQUIRED_PRESERVING)
            return True, AuthenticationErrorMessages.TOTP_AUTHENTICATION_REQUIRED, True
        elif connection_result.result == AuthenticationResult.IN_APP_AUTHENTICATION_REQUIRED:
            # In-app authentication required means credentials are valid, just need mobile app authentication
            # Set session flag so login page shows in-app authentication message
            self.auth_service.session_manager.set_in_app_auth_required(request, True)
            self.logger.info(LogMessages.IN_APP_AUTH_REQUIRED_PRESERVING)
            return True, AuthenticationErrorMessages.IN_APP_AUTHENTICATION_REQUIRED, True
        elif connection_result.result in [
            AuthenticationResult.CONNECTION_ERROR,
            AuthenticationResult.CONFIGURATION_ERROR,
            AuthenticationResult.INVALID_CREDENTIALS,
            AuthenticationResult.MAINTENANCE_MODE,
            AuthenticationResult.ACCOUNT_BLOCKED,
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
