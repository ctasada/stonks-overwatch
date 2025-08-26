"""
Authentication service interface.

This module defines the interface for authentication service implementations.
The authentication service orchestrates the complete authentication flow,
coordinating between session management, credential handling, and DeGiro API operations.
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass
from enum import Enum
from typing import Optional

from django.http import HttpRequest

from stonks_overwatch.config.degiro import DegiroCredentials


class AuthenticationResult(Enum):
    """
    Enumeration of possible authentication results.
    """

    SUCCESS = "success"
    TOTP_REQUIRED = "totp_required"
    IN_APP_AUTHENTICATION_REQUIRED = "in_app_authentication_required"
    ACCOUNT_BLOCKED = "account_blocked"
    INVALID_CREDENTIALS = "invalid_credentials"
    CONNECTION_ERROR = "connection_error"
    MAINTENANCE_MODE = "maintenance_mode"
    OFFLINE_MODE = "offline_mode"
    CONFIGURATION_ERROR = "configuration_error"
    UNKNOWN_ERROR = "unknown_error"


@dataclass
class AuthenticationResponse:
    """
    Response object for authentication operations.

    Contains the result status, optional error message, and any additional
    context information needed by the calling code.
    """

    result: AuthenticationResult
    message: Optional[str] = None
    session_id: Optional[str] = None
    requires_totp: bool = False
    is_maintenance_mode: bool = False
    error_details: Optional[dict] = None

    @property
    def is_success(self) -> bool:
        """Check if authentication was successful."""
        return self.result == AuthenticationResult.SUCCESS

    @property
    def is_error(self) -> bool:
        """Check if authentication resulted in an error."""
        return self.result not in [
            AuthenticationResult.SUCCESS,
            AuthenticationResult.TOTP_REQUIRED,
            AuthenticationResult.IN_APP_AUTHENTICATION_REQUIRED,
        ]


class AuthenticationServiceInterface(ABC):
    """
    Interface for authentication service implementations.

    This interface defines the main authentication operations that orchestrate
    the complete authentication flow. The service coordinates between session
    management, credential handling, and the DeGiro API to provide a unified
    authentication experience.

    The authentication service is the primary entry point for all authentication
    operations and should be used by both middleware and views to ensure
    consistent behavior.

    **Dependency Injection Support:**

    To support dependency injection with the BrokerFactory, service
    implementations should:

    1. Accept optional service dependencies in their constructor:
       ```python
       def __init__(
           self,
           session_manager: Optional[SessionManagerInterface] = None,
           credential_service: Optional[CredentialServiceInterface] = None,
           config: Optional[BaseConfig] = None,
           **kwargs
       ):
           # Implementation specific initialization
       ```

    2. Use the DependencyInjectionMixin or BaseService for automatic
       configuration handling:
       ```python
       from stonks_overwatch.core.interfaces.base_service import BaseService

       class MyAuthenticationService(AuthenticationServiceInterface, BaseService):
           def __init__(self, session_manager=None, credential_service=None, config=None, **kwargs):
               super().__init__(config, **kwargs)
       ```

    3. This maintains backward compatibility while enabling automatic
       dependency injection from the unified factory.
    """

    @abstractmethod
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
        pass

    @abstractmethod
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
        pass

    @abstractmethod
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
        pass

    @abstractmethod
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
        pass

    @abstractmethod
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
        pass

    @abstractmethod
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
        pass

    @abstractmethod
    def is_degiro_enabled(self) -> bool:
        """
        Check if DeGiro authentication is enabled in the configuration.

        Returns:
            bool: True if DeGiro is enabled, False otherwise
        """
        pass

    @abstractmethod
    def is_offline_mode(self) -> bool:
        """
        Check if DeGiro is in offline mode.

        Returns:
            bool: True if offline mode is enabled, False otherwise
        """
        pass

    @abstractmethod
    def is_maintenance_mode_allowed(self) -> bool:
        """
        Check if access is allowed during maintenance mode.

        This typically requires having stored credentials available.

        Returns:
            bool: True if access is allowed during maintenance, False otherwise
        """
        pass

    @abstractmethod
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
        pass

    @abstractmethod
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
        pass

    @abstractmethod
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
        pass
