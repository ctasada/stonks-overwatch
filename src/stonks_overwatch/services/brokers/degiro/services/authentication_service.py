"""
DeGiro authentication service implementation.

This module provides the concrete implementation of the authentication service
that orchestrates the complete authentication flow, coordinating between session
management, credential handling, and DeGiro API operations.
"""

from time import sleep
from typing import Optional

from degiro_connector.core.exceptions import DeGiroConnectionError, MaintenanceError
from django.http import HttpRequest

from stonks_overwatch.config.degiro import DegiroCredentials
from stonks_overwatch.core.interfaces.authentication_service import (
    AuthenticationResponse,
    AuthenticationResult,
    AuthenticationServiceInterface,
)
from stonks_overwatch.core.interfaces.base_service import BaseService
from stonks_overwatch.core.interfaces.credential_service import CredentialServiceInterface
from stonks_overwatch.core.interfaces.session_manager import SessionManagerInterface
from stonks_overwatch.services.brokers.degiro.client.degiro_client import CredentialsManager, DeGiroService
from stonks_overwatch.services.brokers.models import BrokersConfigurationRepository
from stonks_overwatch.services.utilities.authentication_credential_service import AuthenticationCredentialService
from stonks_overwatch.services.utilities.authentication_session_manager import AuthenticationSessionManager
from stonks_overwatch.settings import DEBUG_MODE
from stonks_overwatch.utils.core.constants import (
    LogMessages,
    TechnicalErrorMessages,
    UserErrorMessages,
)
from stonks_overwatch.utils.core.logger import StonksLogger


class DegiroAuthenticationService(AuthenticationServiceInterface, BaseService):
    """
    DeGiro-specific authentication service implementation.

    This class orchestrates the complete authentication flow by coordinating
    between session management, credential handling, and DeGiro API operations.
    It serves as the main entry point for all DeGiro authentication operations and
    ensures consistent behavior across the application.

    The service handles:
    - User authentication and login flows
    - TOTP (2FA) authentication
    - Session state management
    - Credential validation and storage
    - Error handling and recovery
    - Maintenance mode scenarios
    """

    BROKER_NAME = "degiro"

    def __init__(
        self,
        session_manager: Optional[SessionManagerInterface] = None,
        credential_service: Optional[CredentialServiceInterface] = None,
        degiro_service: Optional[DeGiroService] = None,
        config=None,
        **kwargs,
    ):
        """
        Initialize the DeGiro authentication service with optional dependencies.

        Args:
            session_manager: Optional session manager (defaults to AuthenticationSessionManager)
            credential_service: Optional credential service (defaults to AuthenticationCredentialService)
            degiro_service: Optional DeGiro service (defaults to new DeGiroService instance)
            config: Optional configuration for dependency injection
            **kwargs: Additional keyword arguments
        """
        super().__init__(config, **kwargs)
        self.logger = StonksLogger.get_logger(__name__, "[DEGIRO|AUTH]")

        # Initialize dependencies with defaults if not provided
        self.session_manager = session_manager or AuthenticationSessionManager(config)
        self.credential_service = credential_service or AuthenticationCredentialService(config)
        self.degiro_service = degiro_service or DeGiroService()

    @property
    def broker_name(self) -> str:
        """Return the broker name."""
        return self.BROKER_NAME

    def is_user_authenticated(self, request: HttpRequest) -> bool:
        """
        Check if the user is currently authenticated.

        This method performs a comprehensive authentication check, including:
        - Session state validation
        - Session ID presence and validity
        - DeGiro connection status (if applicable)

        Args:
            request: The HTTP request containing session data

        Returns:
            bool: True if user is authenticated, False otherwise
        """
        try:
            # Check basic session authentication
            if not self.session_manager.is_authenticated(request):
                self.logger.debug("User not authenticated in session")
                return False

            # Verify session ID exists
            session_id = self.session_manager.get_session_id(request)
            if not session_id:
                self.logger.debug("No session ID found")
                return False

            self.logger.debug("User is authenticated")
            return True

        except Exception as e:
            self.logger.error(f"Error checking authentication status: {str(e)}")
            return False

    def authenticate_user(
        self,
        request: HttpRequest,
        username: Optional[str] = None,
        password: Optional[str] = None,
        one_time_password: Optional[int] = None,
        remember_me: bool = False,
    ) -> AuthenticationResponse:
        """
        Authenticate a user with the provided credentials.

        This is the main authentication method that handles the complete flow:
        1. Validates and merges credentials from multiple sources
        2. Attempts connection to DeGiro API
        3. Handles TOTP requirements
        4. Manages session state
        5. Stores credentials if "remember me" is selected

        Args:
            request: The HTTP request containing session data
            username: Optional username (if not provided, will try to get from other sources)
            password: Optional password (if not provided, will try to get from other sources)
            one_time_password: Optional 2FA code for TOTP authentication
            remember_me: Whether to store credentials for future use

        Returns:
            AuthenticationResponse: Detailed result of the authentication attempt
        """
        try:
            self.logger.info(LogMessages.AUTH_STARTED)

            # Get effective credentials by merging provided values with stored ones
            effective_credentials = self._get_effective_credentials(
                request, username, password, one_time_password, remember_me
            )

            if not effective_credentials:
                return self._create_error_response(
                    AuthenticationResult.CONFIGURATION_ERROR, UserErrorMessages.CONFIGURATION_ERROR
                )

            # Validate credentials format
            if not self.credential_service.validate_credentials(
                effective_credentials.username, effective_credentials.password
            ):
                return self._create_error_response(
                    AuthenticationResult.INVALID_CREDENTIALS, UserErrorMessages.INVALID_CREDENTIALS
                )

            # Store credentials in session for later use
            self.session_manager.store_credentials(
                request=request,
                username=effective_credentials.username,
                password=effective_credentials.password,
                remember_me=effective_credentials.remember_me or False,
            )

            # Attempt DeGiro authentication
            auth_response = self._authenticate_with_degiro(request, effective_credentials)

            # If successful and remember_me is selected, store in database
            if auth_response.is_success and effective_credentials.remember_me:
                self.credential_service.store_credentials_in_database(
                    effective_credentials.username, effective_credentials.password
                )

            return auth_response

        except Exception as e:
            self.logger.error(f"{TechnicalErrorMessages.AUTH_SERVICE_UNEXPECTED_ERROR}: {str(e)}")
            return self._create_error_response(AuthenticationResult.UNKNOWN_ERROR, UserErrorMessages.UNEXPECTED_ERROR)

    def check_degiro_connection(self, request: HttpRequest) -> AuthenticationResponse:
        """
        Check the connection to DeGiro without performing full authentication.

        This method is used by middleware to verify existing connections
        and handle maintenance mode scenarios.

        Args:
            request: The HTTP request containing session data

        Returns:
            AuthenticationResponse: Result of the connection check
        """
        try:
            self.logger.debug("Checking DeGiro connection status")

            # Check if DeGiro is enabled
            if not self.is_degiro_enabled():
                return self._create_error_response(AuthenticationResult.CONFIGURATION_ERROR, "DeGiro is not enabled")

            # Check if in offline mode
            if self.is_offline_mode():
                return self._create_success_response("DeGiro is in offline mode")

            # Try to check connection
            try:
                is_connected = self.degiro_service.check_connection()

                if is_connected:
                    # Update session with current session ID
                    session_id = self.degiro_service.get_session_id()
                    self.session_manager.set_session_id(request, session_id)
                    self.session_manager.set_authenticated(request, True)

                    return AuthenticationResponse(
                        result=AuthenticationResult.SUCCESS, message="Connection verified", session_id=session_id
                    )
                else:
                    return self._create_error_response(
                        AuthenticationResult.CONNECTION_ERROR, "Failed to establish connection"
                    )

            except MaintenanceError:
                return AuthenticationResponse(
                    result=AuthenticationResult.MAINTENANCE_MODE,
                    message="DeGiro is in maintenance mode",
                    is_maintenance_mode=True,
                )
            except DeGiroConnectionError as degiro_error:
                return self._handle_degiro_connection_error_in_check(request, degiro_error)

        except Exception as e:
            self.logger.error(f"Error checking DeGiro connection: {str(e)}", exc_info=DEBUG_MODE)
            return self._create_error_response(
                AuthenticationResult.CONNECTION_ERROR, f"Connection check failed: {str(e)}"
            )

    def _handle_degiro_connection_error_in_check(
        self, request: HttpRequest, degiro_error: DeGiroConnectionError
    ) -> AuthenticationResponse:
        """Handle DeGiro connection errors during connection check."""
        # Handle TOTP requirement specifically
        if hasattr(degiro_error, "error_details") and degiro_error.error_details.status_text == "totpNeeded":
            return self._handle_totp_required_error(request, degiro_error)

        # Handle in-app authentication requirement specifically
        elif hasattr(degiro_error, "error_details") and (
            degiro_error.error_details.status_text == "inAppTOTPNeeded" or degiro_error.error_details.status == 12
        ):
            return self._handle_in_app_auth_required_error(request, degiro_error)

        # Handle account blocked (status 4)
        elif hasattr(degiro_error, "error_details") and degiro_error.error_details.status == 4:
            self.logger.warning("Account is blocked during connection check")
            return AuthenticationResponse(
                result=AuthenticationResult.ACCOUNT_BLOCKED,
                message="Your account has been blocked because the maximum of login attempts has been exceeded",
            )
        else:
            # Other DeGiro connection errors
            self.logger.error(f"DeGiro connection error: {degiro_error}")
            # Split the error message construction into two lines for clarity
            if hasattr(degiro_error, "error_details"):
                error_status = degiro_error.error_details.status_text
            else:
                error_status = str(degiro_error)
            return self._create_error_response(
                AuthenticationResult.INVALID_CREDENTIALS,
                f"DeGiro authentication failed: {error_status}",
            )

    def _handle_totp_required_error(
        self, request: HttpRequest, degiro_error: DeGiroConnectionError
    ) -> AuthenticationResponse:
        """Handle TOTP required error specifically."""
        self.logger.info("TOTP required during connection check")

        # Store current credentials in session for TOTP flow
        effective_credentials = self.credential_service.get_effective_credentials(request)
        if effective_credentials:
            self.logger.info(
                f"Storing effective credentials in session for TOTP: username={effective_credentials.username}"
            )
            self.session_manager.store_credentials(
                request=request,
                username=effective_credentials.username,
                password=effective_credentials.password,
                remember_me=effective_credentials.remember_me or False,
            )

        return AuthenticationResponse(
            result=AuthenticationResult.TOTP_REQUIRED,
            message="TOTP authentication required",
            requires_totp=True,
        )

    def _handle_in_app_auth_required_error(
        self, request: HttpRequest, degiro_error: DeGiroConnectionError
    ) -> AuthenticationResponse:
        """Handle in-app authentication required error specifically."""
        self.logger.info("In-app authentication required during connection check")

        # Store current credentials in session for in-app authentication flow
        effective_credentials = self.credential_service.get_effective_credentials(request)
        if effective_credentials:
            self.logger.info(
                f"Storing effective credentials in session for in-app authentication: "
                f"username={effective_credentials.username}"
            )
            self.session_manager.store_credentials(
                request=request,
                username=effective_credentials.username,
                password=effective_credentials.password,
                remember_me=effective_credentials.remember_me or False,
                in_app_token=degiro_error.error_details.in_app_token,
            )

        return AuthenticationResponse(
            result=AuthenticationResult.IN_APP_AUTHENTICATION_REQUIRED,
            message="In-app authentication required",
        )

    def _handle_totp_required_with_credentials(
        self, request: HttpRequest, credentials: DegiroCredentials
    ) -> AuthenticationResponse:
        """Handle TOTP required error with credentials."""
        self.session_manager.set_totp_required(request, True)

        # Store credentials for TOTP flow if provided
        self.session_manager.store_credentials(
            request=request,
            username=credentials.username,
            password=credentials.password,
            remember_me=credentials.remember_me or False,
        )

        return AuthenticationResponse(
            result=AuthenticationResult.TOTP_REQUIRED,
            message="Two-factor authentication required",
            requires_totp=True,
        )

    def _handle_in_app_auth_required_with_credentials(
        self, request: HttpRequest, credentials: DegiroCredentials, in_app_token: str
    ) -> AuthenticationResponse:
        """Handle in-app authentication required error with credentials."""
        self.session_manager.set_in_app_auth_required(request, True)

        # Store credentials for in-app authentication flow if provided
        self.session_manager.store_credentials(
            request=request,
            username=credentials.username,
            password=credentials.password,
            in_app_token=in_app_token,
            remember_me=credentials.remember_me or False,
        )

        return AuthenticationResponse(
            result=AuthenticationResult.IN_APP_AUTHENTICATION_REQUIRED,
            message="In-app authentication required",
        )

    def handle_totp_authentication(self, request: HttpRequest, one_time_password: int) -> AuthenticationResponse:
        """
        Handle TOTP (2FA) authentication when required.

        This method is called when the initial authentication indicated
        that TOTP is required.

        Args:
            request: The HTTP request containing session data
            one_time_password: The 2FA code provided by the user

        Returns:
            AuthenticationResponse: Result of the TOTP authentication
        """
        try:
            self.logger.info("Handling TOTP authentication")

            # Get stored credentials from session
            credentials = self.session_manager.get_credentials(request)
            if not credentials:
                return self._create_error_response(
                    AuthenticationResult.CONFIGURATION_ERROR, "No credentials found in session for TOTP authentication"
                )

            # Create credentials with TOTP
            totp_credentials = self.credential_service.merge_credentials(
                credentials, one_time_password=one_time_password
            )

            # Attempt authentication with TOTP
            auth_response = self._authenticate_with_degiro(request, totp_credentials)

            # Clear TOTP requirement flag if successful
            if auth_response.is_success:
                self.session_manager.set_totp_required(request, False)

                # If remember_me was selected, store credentials in database
                if totp_credentials.remember_me:
                    self.credential_service.store_credentials_in_database(
                        totp_credentials.username, totp_credentials.password
                    )
                    self.logger.debug("Credentials stored in database due to remember_me selection")

            return auth_response

        except Exception as e:
            self.logger.error(f"Error during TOTP authentication: {str(e)}")
            return self._create_error_response(
                AuthenticationResult.UNKNOWN_ERROR, f"TOTP authentication failed: {str(e)}"
            )

    def handle_in_app_authentication(self, request: HttpRequest) -> AuthenticationResponse:
        """
        Handle in-app authentication when required.

        This method is called when the initial authentication indicated
        that in-app authentication is required. It waits for the user to
        confirm authentication in their mobile app.

        Args:
            request: The HTTP request containing session data

        Returns:
            AuthenticationResponse: Result of the in-app authentication
        """
        try:
            # Get stored credentials from session
            credentials = self.session_manager.get_credentials(request)
            if not credentials or not credentials.in_app_token:
                return self._create_error_response(
                    AuthenticationResult.CONFIGURATION_ERROR,
                    "No in-app token found in session for in-app authentication",
                )

            # Wait for in-app confirmation
            session_id = self._wait_for_in_app_confirmation(credentials)
            if session_id:
                # Success - clear in-app auth flag and set authenticated
                self.session_manager.set_in_app_auth_required(request, False)
                self.session_manager.set_authenticated(request, True)
                self.session_manager.set_session_id(request, session_id)

                # Enable broker in database on successful authentication
                self._enable_broker_in_database()

                # If remember_me was selected, store credentials in database
                if credentials.remember_me:
                    self.credential_service.store_credentials_in_database(credentials.username, credentials.password)
                    self.logger.debug("Credentials stored in database due to remember_me selection")

                return AuthenticationResponse(
                    result=AuthenticationResult.SUCCESS,
                    message="In-app authentication successful",
                    session_id=session_id,
                )
            else:
                # This should not happen as _wait_for_in_app_confirmation raises exceptions on failure
                return self._create_error_response(
                    AuthenticationResult.CONNECTION_ERROR, "In-app authentication failed without exception"
                )

        except Exception as e:
            self.logger.error(f"Error during in-app authentication: {str(e)}")
            # Clear in-app auth session state on error
            self.session_manager.set_in_app_auth_required(request, False)
            return self._create_error_response(
                AuthenticationResult.CONNECTION_ERROR, f"In-app authentication failed: {str(e)}"
            )

    def logout_user(self, request: HttpRequest) -> None:
        """
        Log out the user and clear all authentication state.

        This method should:
        - Clear session authentication state
        - Remove stored credentials if applicable
        - Clean up any cached connection state

        Args:
            request: The HTTP request containing session data
        """
        try:
            self.logger.info("Logging out user")

            # Clear all session data
            self.session_manager.clear_session(request)

            # Note: We don't clear database credentials here as those are
            # for "remember me" functionality and should persist across sessions

            self.logger.info(LogMessages.LOGOUT_SUCCESSFUL)

        except Exception as e:
            self.logger.error(f"Error during logout: {str(e)}")

    def is_degiro_enabled(self) -> bool:
        """
        Check if DeGiro authentication is enabled in the configuration.

        Returns:
            bool: True if DeGiro is enabled, False otherwise
        """
        try:
            from stonks_overwatch.core.factories.broker_factory import BrokerFactory

            broker_factory = BrokerFactory()
            degiro_config = broker_factory.create_config("degiro")

            return degiro_config is not None and degiro_config.is_enabled()

        except Exception as e:
            self.logger.error(f"Error checking if DeGiro is enabled: {str(e)}")
            return False

    def is_offline_mode(self) -> bool:
        """
        Check if DeGiro is in offline mode.

        Returns:
            bool: True if offline mode is enabled, False otherwise
        """
        try:
            from stonks_overwatch.core.factories.broker_factory import BrokerFactory

            broker_factory = BrokerFactory()
            degiro_config = broker_factory.create_config("degiro")

            return degiro_config is not None and degiro_config.offline_mode

        except Exception as e:
            self.logger.error(f"Error checking offline mode: {str(e)}")
            return False

    def is_maintenance_mode_allowed(self) -> bool:
        """
        Check if access is allowed during maintenance mode.

        This typically requires having stored credentials available.

        Returns:
            bool: True if access is allowed during maintenance, False otherwise
        """
        try:
            if self.degiro_service.is_maintenance_mode:
                # Check if we have default credentials available
                return self.credential_service.has_default_credentials()
            return False

        except Exception as e:
            self.logger.error(f"Error checking maintenance mode access: {str(e)}")
            return False

    def should_check_connection(self, request: HttpRequest) -> bool:
        """
        Determine if a connection check should be performed.

        This method helps optimize performance by avoiding unnecessary
        connection checks when they're not needed.

        Args:
            request: The HTTP request containing session data

        Returns:
            bool: True if connection should be checked, False otherwise
        """
        try:
            # Don't check connection if TOTP is currently required
            # This prevents infinite loops when TOTP is needed
            if self.session_manager.is_totp_required(request):
                self.logger.debug("Skipping connection check - TOTP required")
                return False

            # Don't check connection if in-app authentication is currently required
            # This prevents infinite loops when in-app auth is needed
            if self.session_manager.is_in_app_auth_required(request):
                self.logger.debug("Skipping connection check - in-app authentication required")
                return False

            # Check if we have default credentials or session credentials
            has_default = self.credential_service.has_default_credentials()
            session_id = self.session_manager.get_session_id(request)

            return has_default or session_id is not None

        except Exception as e:
            self.logger.error(f"Error determining if connection should be checked: {str(e)}")
            return False

    def get_authentication_status(self, request: HttpRequest) -> dict:
        """
        Get comprehensive authentication status for debugging/monitoring.

        Returns a dictionary containing detailed information about the
        current authentication state, credential sources, connection status, etc.
        Sensitive information should be masked.

        Args:
            request: The HTTP request containing session data

        Returns:
            dict: Dictionary containing authentication status information
        """
        try:
            status = {
                "is_authenticated": self.is_user_authenticated(request),
                "degiro_enabled": self.is_degiro_enabled(),
                "offline_mode": self.is_offline_mode(),
                "maintenance_mode": self.degiro_service.is_maintenance_mode,
                "maintenance_allowed": self.is_maintenance_mode_allowed(),
                "should_check_connection": self.should_check_connection(request),
                "session_data": self.session_manager.get_session_data(request),
                "credential_sources": self.credential_service.get_credential_sources(request),
            }

            return status

        except Exception as e:
            self.logger.error(f"Error getting authentication status: {str(e)}")
            return {"error": "Failed to retrieve authentication status"}

    def handle_authentication_error(
        self, request: HttpRequest, error: Exception, credentials: Optional[DegiroCredentials] = None
    ) -> AuthenticationResponse:
        """
        Handle authentication errors and convert them to appropriate responses.

        This method provides centralized error handling for authentication
        operations, ensuring consistent error responses and logging.

        Args:
            request: The HTTP request containing session data
            error: The exception that occurred during authentication
            credentials: Optional credentials that were being used

        Returns:
            AuthenticationResponse: Appropriate response for the error
        """
        try:
            self.logger.error(f"Handling authentication error: {type(error).__name__}: {str(error)}")

            if isinstance(error, DeGiroConnectionError):
                return self._handle_degiro_connection_error(request, error, credentials)
            elif isinstance(error, MaintenanceError):
                return AuthenticationResponse(
                    result=AuthenticationResult.MAINTENANCE_MODE,
                    message=error.error_details.error if hasattr(error, "error_details") else str(error),
                    is_maintenance_mode=True,
                )
            elif isinstance(error, ConnectionError):
                return self._create_error_response(
                    AuthenticationResult.CONNECTION_ERROR, "Network connection error occurred"
                )
            else:
                return self._create_error_response(AuthenticationResult.UNKNOWN_ERROR, f"Unknown error: {str(error)}")

        except Exception as e:
            self.logger.error(f"Error handling authentication error: {str(e)}")
            return self._create_error_response(
                AuthenticationResult.UNKNOWN_ERROR, "Failed to handle authentication error"
            )

    def _wait_for_in_app_confirmation(self, credentials: DegiroCredentials) -> Optional[str]:
        """
        Waits for the user to confirm in-app and retries connection until successful or unrecoverable error.
        Returns the session ID if confirmation succeeds, otherwise raises exception.

        Uses the existing DeGiroService to maintain consistency with the rest of the authentication flow.

        Args:
            credentials: The credentials including the in_app_token

        Returns:
            Optional[str]: The session ID if successful, None otherwise

        Raises:
            DeGiroConnectionError: For unrecoverable errors or authentication failures
            Exception: For other unexpected errors
        """
        # Create DeGiro credentials object with in_app_token
        degiro_credentials = DegiroCredentials(
            username=credentials.username,
            password=credentials.password,
            one_time_password=credentials.one_time_password,
            int_account=credentials.int_account,
            totp_secret_key=credentials.totp_secret_key,
            in_app_token=credentials.in_app_token,
        )

        # Update DeGiro service credentials (following the same pattern as _authenticate_with_degiro)
        credentials_manager = CredentialsManager(degiro_credentials)
        self.degiro_service.set_credentials(credentials_manager)

        while True:
            sleep(5)
            try:
                # Use DeGiroService connect method (same as _authenticate_with_degiro)
                self.degiro_service.connect()

                # Get session ID using DeGiroService method
                session_id = self.degiro_service.get_session_id()
                self.logger.info("In-app authentication successful")
                return session_id
            except DeGiroConnectionError as retry_error:
                if hasattr(retry_error, "error_details") and retry_error.error_details.status == 3:
                    # Status 3 means still waiting for user confirmation - continue waiting
                    self.logger.debug("Still waiting for in-app confirmation...")
                    continue
                else:
                    # Other error statuses are unrecoverable
                    self.logger.error(f"Unrecoverable error during in-app authentication: {retry_error}")
                    raise retry_error
            except Exception as e:
                self.logger.error(f"Unexpected error during in-app authentication wait: {str(e)}")
                raise e

        return None

    # Private helper methods

    def _get_effective_credentials(
        self,
        request: HttpRequest,
        username: Optional[str],
        password: Optional[str],
        one_time_password: Optional[int],
        remember_me: bool,
    ) -> Optional[DegiroCredentials]:
        """Get effective credentials by merging provided values with stored ones."""
        try:
            # Get base credentials from the most appropriate source
            base_credentials = self.credential_service.get_effective_credentials(request)

            # Merge with provided values
            effective_credentials = self.credential_service.merge_credentials(
                base_credentials,
                username=username,
                password=password,
                one_time_password=one_time_password,
                remember_me=remember_me,
            )

            return effective_credentials

        except Exception as e:
            self.logger.error(f"Error getting effective credentials: {str(e)}")
            return None

    def _authenticate_with_degiro(self, request: HttpRequest, credentials: DegiroCredentials) -> AuthenticationResponse:
        """Perform the actual DeGiro authentication."""
        try:
            # Create DeGiro credentials object
            degiro_credentials = DegiroCredentials(
                username=credentials.username,
                password=credentials.password,
                one_time_password=credentials.one_time_password,
                int_account=credentials.int_account,
                totp_secret_key=credentials.totp_secret_key,
            )

            # Update DeGiro service credentials
            credentials_manager = CredentialsManager(degiro_credentials)
            self.degiro_service.set_credentials(credentials_manager)

            # Update global configuration (moved from DeGiroService)
            self._update_global_config_credentials(degiro_credentials)

            # Attempt connection
            self.degiro_service.connect()

            # If successful, update session
            session_id = self.degiro_service.get_session_id()
            self.session_manager.set_authenticated(request, True)
            self.session_manager.set_session_id(request, session_id)

            # Enable broker in database on successful authentication
            self._enable_broker_in_database()

            return AuthenticationResponse(
                result=AuthenticationResult.SUCCESS, message="Authentication successful", session_id=session_id
            )

        except MaintenanceError as error:
            return AuthenticationResponse(
                result=AuthenticationResult.MAINTENANCE_MODE,
                message=error.error_details.error if hasattr(error, "error_details") else str(error),
                is_maintenance_mode=True,
            )
        except DeGiroConnectionError as error:
            return self._handle_degiro_connection_error(request, error, credentials)
        except Exception as e:
            self.logger.error(f"Error during DeGiro authentication: {str(e)}")
            return self._create_error_response(
                AuthenticationResult.CONNECTION_ERROR, f"Authentication failed: {str(e)}"
            )

    def _handle_degiro_connection_error(
        self, request: HttpRequest, error: DeGiroConnectionError, credentials: DegiroCredentials
    ) -> AuthenticationResponse:
        """Handle DeGiro connection errors."""
        if hasattr(error, "error_details") and error.error_details.status_text == "totpNeeded":
            return self._handle_totp_required_with_credentials(request, credentials)
        elif hasattr(error, "error_details") and error.error_details.status_text == "inAppTOTPNeeded":
            return self._handle_in_app_auth_required_with_credentials(
                request, credentials, error.error_details.in_app_token
            )
        elif hasattr(error, "error_details") and error.error_details.status == 4:
            return AuthenticationResponse(
                result=AuthenticationResult.ACCOUNT_BLOCKED,
                message="Your account has been blocked because the maximum of login attempts has been exceeded",
            )
        else:
            error_message = (
                error.error_details.status_text
                if hasattr(error, "error_details") and error.error_details.status_text
                else str(error)
            )
            return self._create_error_response(AuthenticationResult.INVALID_CREDENTIALS, error_message)

    def _create_success_response(self, message: str) -> AuthenticationResponse:
        """Helper to create success response."""
        return AuthenticationResponse(result=AuthenticationResult.SUCCESS, message=message)

    def _create_error_response(self, result: AuthenticationResult, message: str) -> AuthenticationResponse:
        """Helper to create error response."""
        return AuthenticationResponse(result=result, message=message)

    def _enable_broker_in_database(self) -> None:
        """
        Enable the broker in the database on successful authentication.

        This ensures the broker is marked as enabled regardless of remember_me setting.
        """
        try:
            degiro_configuration = BrokersConfigurationRepository.get_broker_by_name("degiro")
            if degiro_configuration:
                degiro_configuration.enabled = True
                BrokersConfigurationRepository.save_broker_configuration(degiro_configuration)
                self.logger.debug("DEGIRO broker enabled in database")
            else:
                self.logger.warning("DEGIRO broker configuration not found in database")

        except Exception as e:
            self.logger.error(f"Failed to enable broker in database: {str(e)}")
            # Don't raise exception - authentication succeeded even if DB update failed

    def _update_global_config_credentials(self, credentials):
        """
        Update the credentials in the global configuration.
        This method was moved from DeGiroService to centralize authentication coordination.

        Args:
            credentials: The new credentials to set in the global config
        """
        try:
            # Delegate to BrokerFactory to follow SOLID principles
            from stonks_overwatch.core.factories.broker_factory import BrokerFactory

            factory = BrokerFactory()
            factory.update_degiro_credentials(
                username=credentials.username,
                password=credentials.password,
                int_account=credentials.int_account,
                totp_secret_key=credentials.totp_secret_key,
                one_time_password=credentials.one_time_password,
            )
            self.logger.debug("Global configuration credentials updated successfully")

        except Exception as e:
            self.logger.error(f"Failed to update global configuration credentials: {str(e)}")
