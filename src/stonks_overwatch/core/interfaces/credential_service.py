"""
Credential service interface.

This module defines the interface for credential service implementations.
The credential service handles validation, storage, and retrieval of user
credentials from various sources (session, database, configuration).
"""

from abc import ABC, abstractmethod
from typing import Optional, Tuple

from django.http import HttpRequest

from stonks_overwatch.config.degiro import DegiroCredentials


class CredentialServiceInterface(ABC):
    """
    Interface for credential service implementations.

    This interface defines the common operations that credential services
    should support, such as validating credentials, storing them in the
    database for "remember me" functionality, and retrieving them from
    various sources.

    The credential service provides a clean abstraction over credential
    management, supporting multiple sources of credentials and handling
    security concerns like validation and encryption.

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

       class MyCredentialService(CredentialServiceInterface, BaseService):
           def __init__(self, config: Optional[BaseConfig] = None, **kwargs):
               super().__init__(config, **kwargs)
       ```

    3. This maintains backward compatibility while enabling automatic
       configuration injection from the unified factory.
    """

    @abstractmethod
    def validate_credentials(self, username: str, password: str) -> bool:
        """
        Validate that the provided credentials are properly formatted.

        This method performs basic validation checks like ensuring
        username and password are not empty, meet minimum requirements, etc.
        It does NOT verify credentials against DeGiro API.

        Args:
            username: The username to validate
            password: The password to validate

        Returns:
            bool: True if credentials are valid format, False otherwise
        """
        pass

    @abstractmethod
    def get_credentials_from_session(self, request: HttpRequest) -> Optional[DegiroCredentials]:
        """
        Retrieve credentials from the session.

        Args:
            request: The HTTP request containing session data

        Returns:
            Optional[DegiroCredentials]: Credentials if found in session, None otherwise
        """
        pass

    @abstractmethod
    def get_credentials_from_database(self) -> Optional[DegiroCredentials]:
        """
        Retrieve stored credentials from the database.

        These are credentials that were previously saved when the user
        selected "remember me" option.

        Returns:
            Optional[DegiroCredentials]: Credentials if found in database, None otherwise
        """
        pass

    @abstractmethod
    def get_credentials_from_config(self) -> Optional[DegiroCredentials]:
        """
        Retrieve credentials from the configuration file.

        These are default credentials specified in the broker configuration.

        Returns:
            Optional[DegiroCredentials]: Credentials if found in config, None otherwise
        """
        pass

    @abstractmethod
    def get_effective_credentials(self, request: HttpRequest) -> Optional[DegiroCredentials]:
        """
        Get the effective credentials to use for authentication.

        This method implements the credential resolution strategy:
        1. Check session for user-provided credentials
        2. Fall back to database ("remember me" credentials)
        3. Fall back to configuration file defaults

        Args:
            request: The HTTP request containing session data

        Returns:
            Optional[DegiroCredentials]: The credentials to use, None if none available
        """
        pass

    @abstractmethod
    def store_credentials_in_database(self, username: str, password: str) -> bool:
        """
        Store credentials in the database for "remember me" functionality.

        Args:
            username: The username to store
            password: The password to store

        Returns:
            bool: True if credentials were stored successfully, False otherwise
        """
        pass

    @abstractmethod
    def has_stored_credentials(self) -> bool:
        """
        Check if there are any stored credentials available.

        This checks both database and configuration sources.

        Returns:
            bool: True if credentials are available from any source, False otherwise
        """
        pass

    @abstractmethod
    def has_default_credentials(self) -> bool:
        """
        Check if default credentials are available from configuration.

        Returns:
            bool: True if default credentials are configured, False otherwise
        """
        pass

    @abstractmethod
    def create_credentials(
        self, username: str, password: str, one_time_password: Optional[int] = None, remember_me: bool = False
    ) -> DegiroCredentials:
        """
        Create a DegiroCredentials object with the provided parameters.

        Args:
            username: The username
            password: The password
            one_time_password: Optional 2FA code
            remember_me: Whether user wants to be remembered

        Returns:
            DegiroCredentials: The constructed credentials object
        """
        pass

    @abstractmethod
    def merge_credentials(
        self,
        base_credentials: Optional[DegiroCredentials],
        username: Optional[str] = None,
        password: Optional[str] = None,
        one_time_password: Optional[int] = None,
        remember_me: Optional[bool] = None,
    ) -> DegiroCredentials:
        """
        Merge provided values with existing credentials.

        This is useful when you have partial credential information
        (e.g., only username from form) and need to merge it with
        existing stored credentials.

        Args:
            base_credentials: Base credentials to start with
            username: Optional username to override
            password: Optional password to override
            one_time_password: Optional 2FA code to override
            remember_me: Optional remember flag to override

        Returns:
            DegiroCredentials: The merged credentials
        """
        pass

    @abstractmethod
    def clear_stored_credentials(self) -> bool:
        """
        Clear any stored credentials from the database.

        This is useful for logout or when user wants to stop
        being remembered.

        Returns:
            bool: True if credentials were cleared successfully, False otherwise
        """
        pass

    @abstractmethod
    def get_credential_sources(self, request: HttpRequest) -> Tuple[bool, bool, bool]:
        """
        Check which credential sources have data available.

        Args:
            request: The HTTP request containing session data

        Returns:
            Tuple[bool, bool, bool]: (has_session, has_database, has_config)
        """
        pass
