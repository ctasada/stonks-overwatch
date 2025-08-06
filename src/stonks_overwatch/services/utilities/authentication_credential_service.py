"""
Authentication credential service implementation.

This module provides the concrete implementation of credential management
for authentication purposes, handling validation, storage, and retrieval
of user credentials from various sources (session, database, configuration).
"""

from typing import Optional, Tuple

from django.http import HttpRequest

from stonks_overwatch.config.degiro import DegiroCredentials
from stonks_overwatch.core.interfaces.base_service import BaseService
from stonks_overwatch.core.interfaces.credential_service import CredentialServiceInterface

# BrokersConfigurationRepository imported lazily to avoid Django setup issues
from stonks_overwatch.utils.core.constants import TechnicalErrorMessages
from stonks_overwatch.utils.core.logger import StonksLogger


class AuthenticationCredentialService(CredentialServiceInterface, BaseService):
    """
    Concrete implementation of credential management for authentication.

    This class handles all credential-related operations, including validation,
    storage in database ("remember me"), retrieval from multiple sources,
    and credential merging operations.

    It follows the CredentialServiceInterface contract and implements the
    credential resolution strategy: session -> database -> configuration.
    """

    logger = StonksLogger.get_logger("stonks_overwatch.auth_credential_service", "[AUTH|CREDENTIAL_SERVICE]")

    def __init__(self, config=None, **kwargs):
        """
        Initialize the authentication credential service.

        Args:
            config: Optional configuration for dependency injection
            **kwargs: Additional keyword arguments
        """
        super().__init__(config, **kwargs)

    def _get_brokers_repository(self):
        """Lazy import to avoid Django setup issues during module import."""
        from stonks_overwatch.services.brokers.models import BrokersConfigurationRepository

        return BrokersConfigurationRepository

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
        try:
            # Check for None or empty values
            if not username or not password:
                self.logger.debug("Credentials validation failed: username or password is empty")
                return False

            # Check for whitespace-only values
            if not username.strip() or not password.strip():
                self.logger.debug("Credentials validation failed: username or password is whitespace only")
                return False

            # Basic length checks
            if len(username.strip()) < 2:
                self.logger.debug("Credentials validation failed: username too short")
                return False

            if len(password) < 4:  # Minimum reasonable password length
                self.logger.debug("Credentials validation failed: password too short")
                return False

            self.logger.debug("Credentials validation passed")
            return True

        except Exception as e:
            self.logger.error(f"{TechnicalErrorMessages.CREDENTIAL_VALIDATION_FAILED}: {str(e)}")
            return False

    def get_credentials_from_session(self, request: HttpRequest) -> Optional[DegiroCredentials]:
        """
        Retrieve credentials from the session.

        Args:
            request: The HTTP request containing session data

        Returns:
            Optional[DegiroCredentials]: Credentials if found in session, None otherwise
        """
        try:
            credentials_data = request.session.get("credentials")
            if credentials_data:
                credentials = DegiroCredentials.from_dict(credentials_data)
                if credentials and credentials.username and credentials.password:
                    self.logger.debug("Retrieved valid credentials from session")
                    return credentials
                else:
                    self.logger.debug("Session contains incomplete credentials")
            else:
                self.logger.debug("No credentials found in session")
            return None
        except Exception as e:
            self.logger.error(f"Error getting credentials from session: {str(e)}")
            return None

    def get_credentials_from_database(self) -> Optional[DegiroCredentials]:
        """
        Retrieve stored credentials from the database.

        These are credentials that were previously saved when the user
        selected "remember me" option.

        Returns:
            Optional[DegiroCredentials]: Credentials if found in database, None otherwise
        """
        try:
            degiro_configuration = self._get_brokers_repository().get_broker_by_name("degiro")
            if degiro_configuration and degiro_configuration.credentials:
                credentials_data = degiro_configuration.credentials
                username = credentials_data.get("username")
                password = credentials_data.get("password")

                if username and password:
                    credentials = DegiroCredentials(
                        username=username,
                        password=password,
                        remember_me=True,  # These were stored, so user wanted to be remembered
                    )
                    self.logger.debug("Retrieved valid credentials from database")
                    return credentials
                else:
                    self.logger.debug("Database contains incomplete credentials")
            else:
                self.logger.debug("No credentials found in database")
            return None
        except Exception as e:
            self.logger.error(f"Error getting credentials from database: {str(e)}")
            return None

    def get_credentials_from_config(self) -> Optional[DegiroCredentials]:
        """
        Retrieve credentials from the configuration file.

        These are default credentials specified in the broker configuration.

        Returns:
            Optional[DegiroCredentials]: Credentials if found in config, None otherwise
        """
        try:
            from stonks_overwatch.core.factories.broker_factory import BrokerFactory

            broker_factory = BrokerFactory()
            degiro_config = broker_factory.create_config("degiro")

            if degiro_config and degiro_config.credentials:
                config_credentials = degiro_config.get_credentials
                if config_credentials and config_credentials.username and config_credentials.password:
                    credentials = DegiroCredentials(
                        username=config_credentials.username,
                        password=config_credentials.password,
                        int_account=config_credentials.int_account,
                        totp_secret_key=config_credentials.totp_secret_key,
                        remember_me=False,  # Config credentials don't imply remember me
                    )
                    self.logger.debug("Retrieved valid credentials from configuration")
                    return credentials
                else:
                    self.logger.debug("Configuration contains incomplete credentials")
            else:
                self.logger.debug("No credentials found in configuration")
            return None
        except Exception as e:
            self.logger.error(f"Error getting credentials from configuration: {str(e)}")
            return None

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
        try:
            # Priority 1: Session credentials (user just entered them)
            session_credentials = self.get_credentials_from_session(request)
            if session_credentials:
                self.logger.debug("Using credentials from session")
                return session_credentials

            # Priority 2: Database credentials (remember me)
            db_credentials = self.get_credentials_from_database()
            if db_credentials:
                self.logger.debug("Using credentials from database (remember me)")
                return db_credentials

            # Priority 3: Configuration credentials (defaults)
            config_credentials = self.get_credentials_from_config()
            if config_credentials:
                self.logger.debug("Using credentials from configuration")
                return config_credentials

            self.logger.debug("No credentials available from any source")
            return None

        except Exception as e:
            self.logger.error(f"Error getting effective credentials: {str(e)}")
            return None

    def store_credentials_in_database(self, username: str, password: str) -> bool:
        """
        Store credentials in the database for "remember me" functionality.

        Args:
            username: The username to store
            password: The password to store

        Returns:
            bool: True if credentials were stored successfully, False otherwise
        """
        try:
            degiro_configuration = self._get_brokers_repository().get_broker_by_name("degiro")
            if degiro_configuration.credentials is None:
                degiro_configuration.credentials = {}

            degiro_configuration.credentials["username"] = username
            degiro_configuration.credentials["password"] = password
            self._get_brokers_repository().save_broker_configuration(degiro_configuration)

            self.logger.debug("Successfully stored credentials in database")
            return True

        except Exception as e:
            self.logger.error(f"{TechnicalErrorMessages.CREDENTIAL_STORAGE_FAILED}: {str(e)}")
            return False

    def has_stored_credentials(self) -> bool:
        """
        Check if there are any stored credentials available.

        This checks both database and configuration sources.

        Returns:
            bool: True if credentials are available from any source, False otherwise
        """
        try:
            # Check database
            db_credentials = self.get_credentials_from_database()
            if db_credentials:
                return True

            # Check configuration
            config_credentials = self.get_credentials_from_config()
            if config_credentials:
                return True

            return False

        except Exception as e:
            self.logger.error(f"Error checking stored credentials: {str(e)}")
            return False

    def has_default_credentials(self) -> bool:
        """
        Check if default credentials are available from configuration.

        Returns:
            bool: True if default credentials are configured, False otherwise
        """
        try:
            config_credentials = self.get_credentials_from_config()
            return config_credentials is not None
        except Exception as e:
            self.logger.error(f"Error checking default credentials: {str(e)}")
            return False

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
        try:
            credentials = DegiroCredentials(
                username=username, password=password, one_time_password=one_time_password, remember_me=remember_me
            )
            self.logger.debug("Created new credentials object")
            return credentials
        except Exception as e:
            self.logger.error(f"Error creating credentials: {str(e)}")
            # Return minimal credentials as fallback
            return DegiroCredentials(username=username or "", password=password or "")

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
        try:
            if base_credentials:
                merged_credentials = self._merge_with_base_credentials(
                    base_credentials, username, password, one_time_password, remember_me
                )
            else:
                merged_credentials = self._create_new_credentials(username, password, one_time_password, remember_me)

            self.logger.debug("Successfully merged credentials")
            return merged_credentials

        except Exception as e:
            self.logger.error(f"Error merging credentials: {str(e)}")
            return self._create_fallback_credentials(username, password, one_time_password, remember_me)

    def _merge_with_base_credentials(
        self,
        base_credentials: DegiroCredentials,
        username: Optional[str],
        password: Optional[str],
        one_time_password: Optional[int],
        remember_me: Optional[bool],
    ) -> DegiroCredentials:
        """Helper method to merge with existing base credentials."""
        return DegiroCredentials(
            username=username if username is not None else base_credentials.username,
            password=password if password is not None else base_credentials.password,
            int_account=base_credentials.int_account,
            totp_secret_key=base_credentials.totp_secret_key,
            one_time_password=one_time_password
            if one_time_password is not None
            else base_credentials.one_time_password,
            remember_me=remember_me if remember_me is not None else base_credentials.remember_me,
        )

    def _create_new_credentials(
        self,
        username: Optional[str],
        password: Optional[str],
        one_time_password: Optional[int],
        remember_me: Optional[bool],
    ) -> DegiroCredentials:
        """Helper method to create new credentials when no base exists."""
        return DegiroCredentials(
            username=username or "",
            password=password or "",
            int_account=None,
            totp_secret_key=None,
            one_time_password=one_time_password,
            remember_me=remember_me or False,
        )

    def _create_fallback_credentials(
        self,
        username: Optional[str],
        password: Optional[str],
        one_time_password: Optional[int],
        remember_me: Optional[bool],
    ) -> DegiroCredentials:
        """Helper method to create fallback credentials on error."""
        return DegiroCredentials(
            username=username or "",
            password=password or "",
            one_time_password=one_time_password,
            remember_me=remember_me or False,
        )

    def clear_stored_credentials(self) -> bool:
        """
        Clear any stored credentials from the database.

        This is useful for logout or when user wants to stop
        being remembered.

        Returns:
            bool: True if credentials were cleared successfully, False otherwise
        """
        try:
            degiro_configuration = self._get_brokers_repository().get_broker_by_name("degiro")
            if degiro_configuration.credentials:
                # Clear the credentials but keep the configuration object
                degiro_configuration.credentials = {}
                self._get_brokers_repository().save_broker_configuration(degiro_configuration)

            self.logger.debug("Successfully cleared stored credentials")
            return True

        except Exception as e:
            self.logger.error(f"Failed to clear stored credentials: {str(e)}")
            return False

    def get_credential_sources(self, request: HttpRequest) -> Tuple[bool, bool, bool]:
        """
        Check which credential sources have data available.

        Args:
            request: The HTTP request containing session data

        Returns:
            Tuple[bool, bool, bool]: (has_session, has_database, has_config)
        """
        try:
            has_session = self._has_session_credentials(request)
            has_database = self._has_database_credentials()
            has_config = self._has_config_credentials()

            self.logger.debug(
                f"Credential sources: session={has_session}, database={has_database}, config={has_config}"
            )
            return (has_session, has_database, has_config)

        except Exception as e:
            self.logger.error(f"Error checking credential sources: {str(e)}")
            return (False, False, False)

    def _has_session_credentials(self, request: HttpRequest) -> bool:
        """Helper method to check if session has credentials."""
        return self.get_credentials_from_session(request) is not None

    def _has_database_credentials(self) -> bool:
        """Helper method to check if database has credentials."""
        return self.get_credentials_from_database() is not None

    def _has_config_credentials(self) -> bool:
        """Helper method to check if config has credentials."""
        return self.get_credentials_from_config() is not None
