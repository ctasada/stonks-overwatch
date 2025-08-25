"""
Authentication session manager implementation.

This module provides the concrete implementation of session management
for authentication purposes, handling storage and retrieval of authentication
state, session IDs, and user credentials from Django sessions.
"""

from typing import Dict, Optional

from django.http import HttpRequest

from stonks_overwatch.config.degiro import DegiroCredentials
from stonks_overwatch.core.interfaces.base_service import BaseService
from stonks_overwatch.core.interfaces.session_manager import SessionManagerInterface
from stonks_overwatch.utils.core.logger import StonksLogger


class AuthenticationSessionManager(SessionManagerInterface, BaseService):
    """
    Concrete implementation of session management for authentication.

    This class handles all session-related operations for authentication,
    including storing and retrieving authentication state, session IDs,
    and user credentials from Django sessions.

    It follows the SessionManagerInterface contract and provides a clean
    abstraction over Django's session framework.
    """

    # Session keys for authentication data
    SESSION_IS_AUTHENTICATED = "is_authenticated"
    SESSION_ID_KEY = "session_id"
    SESSION_CREDENTIALS_KEY = "credentials"
    SESSION_SHOW_OTP_KEY = "show_otp"
    SESSION_IN_APP_AUTH_KEY = "in_app_auth_required"

    logger = StonksLogger.get_logger("stonks_overwatch.auth_session_manager", "[AUTH|SESSION_MANAGER]")

    def __init__(self, config=None, **kwargs):
        """
        Initialize the authentication session manager.

        Args:
            config: Optional configuration for dependency injection
            **kwargs: Additional keyword arguments
        """
        super().__init__(config, **kwargs)

    def is_authenticated(self, request: HttpRequest) -> bool:
        """
        Check if the user is authenticated.

        Verifies that the session contains valid authentication state
        and session ID information.

        Args:
            request: The HTTP request containing session data

        Returns:
            bool: True if user is authenticated, False otherwise
        """
        try:
            # Check if basic session authentication exists
            if not request.session.get(self.SESSION_IS_AUTHENTICATED):
                self.logger.debug("Session not authenticated")
                return False

            # Verify session_id exists
            session_id = request.session.get(self.SESSION_ID_KEY)
            if not session_id:
                self.logger.debug("No session ID found")
                return False

            return True

        except Exception as e:
            self.logger.error(f"Error checking authentication status: {str(e)}")
            return False

    def set_authenticated(self, request: HttpRequest, authenticated: bool) -> None:
        """
        Set the authentication status in the session.

        Args:
            request: The HTTP request containing session data
            authenticated: Whether the user is authenticated
        """
        try:
            request.session[self.SESSION_IS_AUTHENTICATED] = authenticated
            request.session.modified = True
            self.logger.debug(f"Set authentication status to: {authenticated}")
        except Exception as e:
            self.logger.error(f"Error setting authentication status: {str(e)}")

    def get_session_id(self, request: HttpRequest) -> Optional[str]:
        """
        Retrieve the DeGiro session ID from the session.

        Args:
            request: The HTTP request containing session data

        Returns:
            Optional[str]: The session ID if available, None otherwise
        """
        try:
            session_id = request.session.get(self.SESSION_ID_KEY)
            if session_id:
                self.logger.debug("Retrieved session ID from session")
            else:
                self.logger.debug("No session ID found in session")
            return session_id
        except Exception as e:
            self.logger.error(f"Error getting session ID: {str(e)}")
            return None

    def set_session_id(self, request: HttpRequest, session_id: str) -> None:
        """
        Store the DeGiro session ID in the session.

        Args:
            request: The HTTP request containing session data
            session_id: The DeGiro session ID to store
        """
        try:
            request.session[self.SESSION_ID_KEY] = session_id
            request.session.modified = True
            self.logger.debug("Stored session ID in session")
        except Exception as e:
            self.logger.error(f"Error setting session ID: {str(e)}")

    def get_credentials(self, request: HttpRequest) -> Optional[DegiroCredentials]:
        """
        Retrieve stored credentials from the session.

        Args:
            request: The HTTP request containing session data

        Returns:
            Optional[DegiroCredentials]: The credentials if available, None otherwise
        """
        try:
            credentials_data = request.session.get(self.SESSION_CREDENTIALS_KEY)
            if credentials_data:
                credentials = DegiroCredentials.from_dict(credentials_data)
                self.logger.debug("Retrieved credentials from session")
                return credentials
            else:
                self.logger.debug("No credentials found in session")
                return None
        except Exception as e:
            self.logger.error(f"Error getting credentials from session: {str(e)}")
            return None

    def store_credentials(self, request: HttpRequest, username: str, password: str, remember_me: bool = False) -> None:
        """
        Store user credentials in the session.

        Args:
            request: The HTTP request containing session data
            username: The username to store
            password: The password to store
            remember_me: Whether the user wants to be remembered
        """
        try:
            credentials = DegiroCredentials(username=username, password=password, remember_me=remember_me)
            request.session[self.SESSION_CREDENTIALS_KEY] = credentials.to_dict()
            request.session.modified = True
            request.session.save()
            self.logger.debug(f"Stored credentials in session (remember_me: {remember_me})")
        except Exception as e:
            self.logger.error(f"Error storing credentials in session: {str(e)}")

    def set_totp_required(self, request: HttpRequest, required: bool = True) -> None:
        """
        Set whether TOTP (2FA) is required for authentication.

        Args:
            request: The HTTP request containing session data
            required: Whether TOTP is required
        """
        try:
            request.session[self.SESSION_SHOW_OTP_KEY] = required
            request.session.modified = True
            self.logger.debug(f"Set TOTP required to: {required}")
        except Exception as e:
            self.logger.error(f"Error setting TOTP required: {str(e)}")

    def is_totp_required(self, request: HttpRequest) -> bool:
        """
        Check if TOTP (2FA) is required.

        Args:
            request: The HTTP request containing session data

        Returns:
            bool: True if TOTP is required, False otherwise
        """
        try:
            totp_required = request.session.get(self.SESSION_SHOW_OTP_KEY, False)
            self.logger.debug(f"TOTP required: {totp_required}")
            return totp_required
        except Exception as e:
            self.logger.error(f"Error checking TOTP required: {str(e)}")
            return False

    def set_in_app_auth_required(self, request: HttpRequest, required: bool = True) -> None:
        """
        Set whether in-app authentication is required for authentication.

        Args:
            request: The HTTP request containing session data
            required: Whether in-app authentication is required
        """
        try:
            request.session[self.SESSION_IN_APP_AUTH_KEY] = required
            request.session.modified = True
            self.logger.debug(f"Set in-app authentication required to: {required}")
        except Exception as e:
            self.logger.error(f"Error setting in-app authentication required: {str(e)}")

    def is_in_app_auth_required(self, request: HttpRequest) -> bool:
        """
        Check if in-app authentication is required.

        Args:
            request: The HTTP request containing session data

        Returns:
            bool: True if in-app authentication is required, False otherwise
        """
        try:
            in_app_auth_required = request.session.get(self.SESSION_IN_APP_AUTH_KEY, False)
            self.logger.debug(f"In-app authentication required: {in_app_auth_required}")
            return in_app_auth_required
        except Exception as e:
            self.logger.error(f"Error checking in-app authentication required: {str(e)}")
            return False

    def clear_session(self, request: HttpRequest) -> None:
        """
        Clear all authentication-related session data.

        This method removes all stored authentication state,
        credentials, and session IDs from the session.

        Args:
            request: The HTTP request containing session data
        """
        try:
            # List of all authentication-related session keys to clear
            auth_keys = [
                self.SESSION_IS_AUTHENTICATED,
                self.SESSION_ID_KEY,
                self.SESSION_CREDENTIALS_KEY,
                self.SESSION_SHOW_OTP_KEY,
                self.SESSION_IN_APP_AUTH_KEY,
            ]

            for key in auth_keys:
                if key in request.session:
                    del request.session[key]

            request.session.modified = True
            self.logger.debug("Cleared all authentication session data")
        except Exception as e:
            self.logger.error(f"Error clearing session data: {str(e)}")

    def get_session_data(self, request: HttpRequest) -> Dict[str, any]:
        """
        Get all authentication-related session data for debugging/logging.

        Returns a sanitized view of session data (passwords are masked).

        Args:
            request: The HTTP request containing session data

        Returns:
            Dict[str, any]: Dictionary containing session data (with sensitive data masked)
        """
        try:
            session_data = {}

            # Get authentication status
            session_data["is_authenticated"] = request.session.get(self.SESSION_IS_AUTHENTICATED, False)

            # Get session ID (partially masked for security)
            session_id = request.session.get(self.SESSION_ID_KEY)
            if session_id:
                # Show only first 8 characters of session ID
                session_data["session_id"] = f"{session_id[:8]}..." if len(session_id) > 8 else session_id
            else:
                session_data["session_id"] = None

            # Get credentials (with password masked)
            credentials_data = request.session.get(self.SESSION_CREDENTIALS_KEY)
            if credentials_data:
                masked_credentials = credentials_data.copy()
                # Mask password for security
                if "password" in masked_credentials:
                    masked_credentials["password"] = "***MASKED***"
                session_data["credentials"] = masked_credentials
            else:
                session_data["credentials"] = None

            # Get TOTP status
            session_data["totp_required"] = request.session.get(self.SESSION_SHOW_OTP_KEY, False)

            # Get in-app authentication status
            session_data["in_app_auth_required"] = request.session.get(self.SESSION_IN_APP_AUTH_KEY, False)

            return session_data

        except Exception as e:
            self.logger.error(f"Error getting session data: {str(e)}")
            return {"error": "Failed to retrieve session data"}
