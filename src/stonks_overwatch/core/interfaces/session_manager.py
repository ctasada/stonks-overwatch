"""
Session manager interface.

This module defines the interface for session management implementations.
The session manager abstracts away session handling concerns from
authentication business logic.
"""

from abc import ABC, abstractmethod
from typing import Dict, Optional

from django.http import HttpRequest

from stonks_overwatch.config.degiro import DegiroCredentials


class SessionManagerInterface(ABC):
    """
    Interface for session manager implementations.

    This interface defines the common operations that session managers
    should support, such as storing and retrieving authentication state,
    session IDs, and user credentials from the session.

    The session manager provides a clean abstraction over Django's session
    framework, making authentication logic testable and independent of
    session implementation details.

    **Dependency Injection Support:**

    To support dependency injection with the BrokerFactory, service
    implementations should:

    1. Accept an optional `config` parameter in their constructor:
       ```python
       def __init__(self, config: Optional[BaseConfig] = None, **kwargs):
           # Implementation specific initialization
       ```

    2. Use the DependencyInjectionMixin or BaseService for automatic
       configuration handling:
       ```python
       from stonks_overwatch.core.interfaces.base_service import BaseService

       class MySessionManager(SessionManagerInterface, BaseService):
           def __init__(self, config: Optional[BaseConfig] = None, **kwargs):
               super().__init__(config, **kwargs)
       ```

    3. This maintains backward compatibility while enabling automatic
       configuration injection from the unified factory.
    """

    @abstractmethod
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
        pass

    @abstractmethod
    def set_authenticated(self, request: HttpRequest, authenticated: bool) -> None:
        """
        Set the authentication status in the session.

        Args:
            request: The HTTP request containing session data
            authenticated: Whether the user is authenticated
        """
        pass

    @abstractmethod
    def get_session_id(self, request: HttpRequest) -> Optional[str]:
        """
        Retrieve the DeGiro session ID from the session.

        Args:
            request: The HTTP request containing session data

        Returns:
            Optional[str]: The session ID if available, None otherwise
        """
        pass

    @abstractmethod
    def set_session_id(self, request: HttpRequest, session_id: str) -> None:
        """
        Store the DeGiro session ID in the session.

        Args:
            request: The HTTP request containing session data
            session_id: The DeGiro session ID to store
        """
        pass

    @abstractmethod
    def get_credentials(self, request: HttpRequest) -> Optional[DegiroCredentials]:
        """
        Retrieve stored credentials from the session.

        Args:
            request: The HTTP request containing session data

        Returns:
            Optional[DegiroCredentials]: The credentials if available, None otherwise
        """
        pass

    @abstractmethod
    def store_credentials(
        self,
        request: HttpRequest,
        username: str,
        password: str,
        in_app_token: str | None = None,
        remember_me: bool = False,
    ) -> None:
        """
        Store user credentials in the session.

        Args:
            request: The HTTP request containing session data
            username: The username to store
            password: The password to store
            in_app_token: The in-app token to store (if applicable). Only used for in-app auth.
            remember_me: Whether the user wants to be remembered
        """
        pass

    @abstractmethod
    def set_totp_required(self, request: HttpRequest, required: bool = True) -> None:
        """
        Set whether TOTP (2FA) is required for authentication.

        Args:
            request: The HTTP request containing session data
            required: Whether TOTP is required
        """
        pass

    @abstractmethod
    def is_totp_required(self, request: HttpRequest) -> bool:
        """
        Check if TOTP (2FA) is required.

        Args:
            request: The HTTP request containing session data

        Returns:
            bool: True if TOTP is required, False otherwise
        """
        pass

    @abstractmethod
    def set_in_app_auth_required(self, request: HttpRequest, required: bool = True) -> None:
        """
        Set whether in-app authentication is required for authentication.

        Args:
            request: The HTTP request containing session data
            required: Whether in-app authentication is required
        """
        pass

    @abstractmethod
    def is_in_app_auth_required(self, request: HttpRequest) -> bool:
        """
        Check if in-app authentication is required.

        Args:
            request: The HTTP request containing session data

        Returns:
            bool: True if in-app authentication is required, False otherwise
        """
        pass

    @abstractmethod
    def clear_session(self, request: HttpRequest) -> None:
        """
        Clear all authentication-related session data.

        This method should remove all stored authentication state,
        credentials, and session IDs from the session.

        Args:
            request: The HTTP request containing session data
        """
        pass

    @abstractmethod
    def get_session_data(self, request: HttpRequest) -> Dict[str, any]:
        """
        Get all authentication-related session data for debugging/logging.

        Returns a sanitized view of session data (passwords should be masked).

        Args:
            request: The HTTP request containing session data

        Returns:
            Dict[str, any]: Dictionary containing session data (with sensitive data masked)
        """
        pass
