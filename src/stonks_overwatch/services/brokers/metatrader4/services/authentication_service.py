"""
MetaTrader 4 authentication service implementation.

This module provides authentication functionality for MetaTrader 4.
MT4 uses SFTP-based data access and doesn't require interactive authentication.
"""

from typing import Optional

import paramiko
from django.http import HttpRequest
from paramiko import SFTPClient

from stonks_overwatch.config.base_config import BaseConfig
from stonks_overwatch.constants import BrokerName
from stonks_overwatch.core.interfaces.authentication_service import (
    AuthenticationResponse,
    AuthenticationResult,
    AuthenticationServiceInterface,
)
from stonks_overwatch.core.interfaces.base_service import BaseService
from stonks_overwatch.utils.core.logger import StonksLogger
from stonks_overwatch.utils.core.session_keys import SessionKeys


class Metatrader4AuthenticationService(BaseService, AuthenticationServiceInterface):
    """
    Authentication service for MetaTrader 4.

    MT4 uses SFTP-based data access and doesn't require interactive user authentication.
    This service provides minimal authentication support for consistency with other brokers.
    """

    def __init__(self, config: Optional[BaseConfig] = None, **kwargs):
        """
        Initialize the MT4 authentication service.

        Args:
            config: Optional MT4 configuration (injected by factory if not provided)
            **kwargs: Additional keyword arguments
        """
        super().__init__(config, **kwargs)
        self.logger = StonksLogger.get_logger(__name__, "[METATRADER4|AUTH]")

    @property
    def broker_name(self) -> str:
        """Return the broker name."""
        return BrokerName.METATRADER4

    def _validate_sftp_file_path(self, sftp_client: SFTPClient, path: str) -> tuple[list, dict]:
        """
        Validate SFTP file path by checking if file exists.

        Args:
            sftp_client: Active SFTP client connection
            path: File path to validate

        Returns:
            Tuple of (file_list, error_dict or None)
        """
        try:
            # Try to get file stats to verify it exists
            sftp_client.stat(path)
            filename = path.split("/")[-1]
            self.logger.debug(f"SFTP file verified: {path}")
            return [filename], None
        except FileNotFoundError:
            self.logger.warning(
                f"File '{path}' not found on SFTP server, but this may be normal if reports haven't been generated yet"
            )
            return [], None
        except Exception as e:
            self.logger.warning(f"Cannot verify SFTP file existence: {str(e)}")
            return [], None

    def _validate_sftp_directory_path(self, sftp_client: SFTPClient, path: str) -> tuple[list, dict]:
        """
        Validate SFTP directory path by checking directory existence and listing files.

        Args:
            sftp_client: Active SFTP client connection
            path: Directory path to validate

        Returns:
            Tuple of (file_list, error_dict or None)
        """
        try:
            # SFTP directory listing
            file_list = sftp_client.listdir(path)
            self.logger.debug(f"SFTP directory verified: {path}")
            self.logger.debug(f"SFTP directory listing successful: {len(file_list)} items found")
            return file_list, None
        except FileNotFoundError:
            self.logger.warning(f"SFTP path does not exist: {path}")
            return [], {"success": False, "message": f"Path '{path}' does not exist on server"}
        except Exception as e:
            self.logger.warning(f"SFTP directory validation failed: {str(e)}")
            return [], {"success": False, "message": f"Cannot access path '{path}': {str(e)}"}

    def validate_credentials(self, ftp_server: str, username: str, password: str, path: str) -> dict:
        """
        Validate MetaTrader 4 SFTP credentials by attempting to connect.

        This method tests the SFTP connection to ensure credentials are valid
        and the specified path exists before storing them.

        Args:
            ftp_server: SFTP server address
            username: Username
            password: Password
            path: Path to reports directory or file on server

        Returns:
            Dictionary with validation result and message
        """
        try:
            # Validate that all required fields are provided
            if not all([ftp_server, username, password, path]):
                return {
                    "success": False,
                    "message": "All credentials are required (server, username, password, path)",
                }

            self.logger.debug(f"Validating SFTP connection to {ftp_server}")

            # Use SFTP for secure connection
            with paramiko.SSHClient() as ssh_client:
                # Configure SSH client security
                ssh_client.set_missing_host_key_policy(paramiko.AutoAddPolicy())

                # Connect to server with explicit port (default 22 for SFTP)
                port = 22  # SFTP standard port
                ssh_client.connect(hostname=ftp_server, port=port, username=username, password=password, timeout=30)

                # Open SFTP session
                with ssh_client.open_sftp() as sftp_client:
                    self.logger.debug("SFTP connection established")

                    # Determine if path is a file or directory
                    # Check if path has a file extension (e.g., .htm, .html, .csv)
                    path_parts = path.split("/")
                    last_part = path_parts[-1] if path_parts else ""
                    is_file_path = "." in last_part  # Simple check for file extension

                    # Validate path based on type (file vs directory)
                    if is_file_path:
                        file_list, error = self._validate_sftp_file_path(sftp_client, path)
                    else:
                        file_list, error = self._validate_sftp_directory_path(sftp_client, path)

                    # If validation failed, return error
                    if error:
                        return error

                    self.logger.info("MetaTrader 4 SFTP credentials validated successfully")
                    return {
                        "success": True,
                        "message": "SFTP credentials validated successfully",
                        "connection_info": {
                            "server": ftp_server,
                            "path": path,
                            "file_count": len(file_list),
                            "connection_type": "SFTP (secure)",
                            "is_secure": True,
                        },
                    }

        except Exception as e:
            error_msg = str(e).lower()

            # Handle specific error types
            if "authentication" in error_msg or "login" in error_msg or "auth" in error_msg:
                self.logger.warning(f"SFTP authentication failed: {str(e)}")
                return {
                    "success": False,
                    "message": "Invalid username or password - please check your credentials",
                }
            elif "connection" in error_msg or "timeout" in error_msg or "refused" in error_msg:
                self.logger.warning(f"SFTP connection failed: {str(e)}")
                return {
                    "success": False,
                    "message": f"Cannot connect to SFTP server '{ftp_server}' - please check the server address",
                }
            elif "timed out" in error_msg:
                self.logger.warning(f"SFTP connection timeout: {str(e)}")
                return {"success": False, "message": "Connection timeout - please try again or check your network"}
            else:
                self.logger.error(f"SFTP validation error: {str(e)}")
                return {"success": False, "message": f"SFTP validation error: {str(e)}"}

    def authenticate_user(
        self,
        request: HttpRequest,
        ftp_server: str,
        username: str,
        password: str,
        path: str,
        remember_me: bool = False,
    ) -> dict:
        """
        Authenticate a user with MT4 by validating and storing FTP/SFTP credentials.

        Args:
            request: The HTTP request containing session data
            ftp_server: FTP/SFTP server address
            username: Username
            password: Password
            path: Path to reports directory on server
            remember_me: Whether to store credentials permanently

        Returns:
            Dictionary with authentication result
        """
        self.logger.debug("Authenticating MT4 user with FTP/SFTP credentials")

        try:
            # Validate credentials first by testing FTP connection
            validation_result = self.validate_credentials(ftp_server, username, password, path)

            if not validation_result["success"]:
                return validation_result

            # Store credentials in session
            request.session[SessionKeys.get_authenticated_key(BrokerName.METATRADER4)] = True
            request.session[SessionKeys.get_credentials_key(BrokerName.METATRADER4)] = {
                "ftp_server": ftp_server,
                "username": username,
                "password": password,
                "path": path,
            }

            # Always ensure broker configuration exists after successful authentication
            # This is needed for dashboard and other services to work properly
            self._ensure_broker_configuration(ftp_server, username, password, path, remember_me)

            # Clear the broker factory cache so it picks up the updated configuration
            self._clear_broker_cache()

            # Trigger job scheduler reconfiguration to pick up the new broker.
            # This schedules the MT4 job with next_run_time=now(), so APScheduler
            # will run the update immediately — no need to trigger it manually.
            self._reconfigure_jobs()

            self.logger.info("MT4 user authentication successful")
            return {
                "success": True,
                "message": "Authentication successful",
                "connection_info": validation_result.get("connection_info", {}),
            }

        except Exception as e:
            self.logger.error(f"MT4 authentication failed: {str(e)}")
            return {
                "success": False,
                "message": f"Authentication failed: {str(e)}",
            }

    def is_user_authenticated(self, request: HttpRequest) -> bool:
        """
        Check the connection to MT4.

        Args:
            request: Django HTTP request

        Returns:
            True if authenticated, False otherwise
        """
        try:
            # Check session authentication
            if not request.session.get(SessionKeys.get_authenticated_key(BrokerName.METATRADER4), False):
                return False

            # Verify credentials are still valid
            credentials = request.session.get(SessionKeys.get_credentials_key(BrokerName.METATRADER4))
            if not credentials:
                return False

            # Quick validation check
            validation_result = self.validate_credentials(
                credentials["ftp_server"], credentials["username"], credentials["password"], credentials["path"]
            )

            return validation_result["success"]

        except Exception as e:
            self.logger.error(f"Authentication check error: {str(e)}")
            return False

    def check_broker_connection(self, request: HttpRequest) -> AuthenticationResponse:
        """
        Check connection - not applicable for MetaTrader4.

        For MT4, we don't have the same live session connection check
        mechanism used by DEGIRO. Returning CONFIGURATION_ERROR matches the
        behavior used by other non-session brokers.

        Args:
            request: The HTTP request containing session data

        Returns:
            AuthenticationResponse: Not applicable response
        """
        self.logger.debug("Broker connection check not applicable for MT4")
        return AuthenticationResponse(
            result=AuthenticationResult.CONFIGURATION_ERROR,
            message="Broker connection check is not applicable for MetaTrader4",
        )

    def handle_totp_authentication(self, request: HttpRequest, one_time_password: int) -> AuthenticationResponse:
        """
        Handle TOTP authentication - not applicable for MetaTrader4.

        MT4 uses FTP-based authentication and doesn't require TOTP.

        Args:
            request: The HTTP request containing session data
            one_time_password: The 2FA code (not used for MT4)

        Returns:
            AuthenticationResponse: Not applicable response
        """
        self.logger.debug("TOTP authentication not applicable for MT4")
        return AuthenticationResponse(
            result=AuthenticationResult.CONFIGURATION_ERROR,
            message="TOTP authentication is not applicable for MetaTrader4",
        )

    def handle_in_app_authentication(self, request: HttpRequest) -> AuthenticationResponse:
        """
        Handle in-app authentication.

        MT4 doesn't support in-app authentication.

        Args:
            request: The HTTP request containing session data

        Returns:
            AuthenticationResponse: Not supported response
        """
        self.logger.debug("In-app authentication not supported for MT4")
        return AuthenticationResponse(
            result=AuthenticationResult.CONFIGURATION_ERROR,
            message="In-app authentication is not supported for MetaTrader4",
        )

    def logout_user(self, request: HttpRequest) -> bool:
        """
        Log out the user and clear all authentication state.

        Args:
            request: The HTTP request containing session data

        Returns:
            True if logout successful, False otherwise
        """
        try:
            self.logger.debug("Logging out MT4 user")

            # Clear all session data for MT4
            request.session.pop(SessionKeys.get_authenticated_key(BrokerName.METATRADER4), None)
            request.session.pop(SessionKeys.get_credentials_key(BrokerName.METATRADER4), None)
            request.session.pop(SessionKeys.get_totp_required_key(BrokerName.METATRADER4), None)
            request.session.pop(SessionKeys.get_in_app_auth_required_key(BrokerName.METATRADER4), None)

            self.logger.info("MT4 user logged out successfully")
            return True

        except Exception as e:
            self.logger.error(f"MT4 logout error: {str(e)}")
            return False

    def is_broker_enabled(self) -> bool:
        """
        Check if MT4 is enabled in the configuration.

        Returns:
            bool: True if MT4 is enabled, False otherwise
        """
        if not self.config:
            return False
        return self.config.is_enabled()

    def is_offline_mode(self) -> bool:
        """
        Check if MT4 is in offline mode.

        Returns:
            bool: Always False as MT4 doesn't support offline mode
        """
        return False

    def is_maintenance_mode_allowed(self) -> bool:
        """
        Check if access is allowed during maintenance mode.

        Returns:
            bool: Always True as MT4 doesn't have maintenance mode
        """
        return True

    def should_check_connection(self, request: HttpRequest) -> bool:
        """
        Determine if a connection check should be performed.

        Args:
            request: The HTTP request containing session data

        Returns:
            bool: True if connection should be checked, False otherwise
        """
        # For MT4, we don't need frequent connection checks
        # Only check if not authenticated
        return not self.is_user_authenticated(request)

    def get_authentication_status(self, request: HttpRequest) -> dict:
        """
        Get comprehensive authentication status for debugging/monitoring.

        Args:
            request: The HTTP request containing session data

        Returns:
            dict: Dictionary containing authentication status information
        """
        return {
            "broker": BrokerName.METATRADER4,
            "is_authenticated": self.is_user_authenticated(request),
            "is_enabled": self.is_broker_enabled(),
            "is_offline_mode": self.is_offline_mode(),
            "authentication_method": "FTP-based (automatic)",
        }

    def handle_authentication_error(
        self, request: HttpRequest, error: Exception, credentials: Optional[object] = None
    ) -> AuthenticationResponse:
        """
        Handle authentication errors and convert them to appropriate responses.

        Args:
            request: The HTTP request containing session data
            error: The exception that occurred during authentication
            credentials: Optional credentials that were being used (not used for MT4)

        Returns:
            AuthenticationResponse: Appropriate response for the error
        """
        self.logger.error(f"MetaTrader4 authentication error: {str(error)}")

        return AuthenticationResponse(
            result=AuthenticationResult.UNKNOWN_ERROR,
            message=f"Authentication error: {str(error)}",
            error_details={"error_type": type(error).__name__, "error_message": str(error)},
        )

    def _ensure_broker_configuration(
        self, ftp_server: str, username: str, password: str, path: str, remember_me: bool
    ) -> None:
        """
        Ensure broker configuration exists in database after successful authentication.

        This method always creates or updates the broker configuration to ensure
        the dashboard and other services can work properly, regardless of remember_me setting.

        Args:
            ftp_server: FTP server address
            username: FTP username
            password: FTP password
            path: Path to reports directory on FTP server
            remember_me: Whether to store credentials permanently
        """
        try:
            from stonks_overwatch.config.metatrader4 import Metatrader4Config
            from stonks_overwatch.services.brokers.models import BrokersConfiguration

            # Get or create broker configuration
            broker_config, created = BrokersConfiguration.objects.get_or_create(
                broker_name=BrokerName.METATRADER4,
                defaults={
                    "enabled": True,
                    "start_date": self.config.start_date if self.config else Metatrader4Config.DEFAULT_MT4_START_DATE,
                    "update_frequency": self.config.update_frequency_minutes
                    if self.config
                    else Metatrader4Config.DEFAULT_MT4_UPDATE_FREQUENCY,
                    "credentials": {
                        "ftp_server": ftp_server if remember_me else "",
                        "username": username if remember_me else "",
                        "password": password if remember_me else "",
                        "path": path if remember_me else "",
                    },
                },
            )

            # If it already exists, update it
            if not created:
                broker_config.enabled = True
                if remember_me:
                    broker_config.credentials = {
                        "ftp_server": ftp_server,
                        "username": username,
                        "password": password,
                        "path": path,
                    }
                broker_config.save()

            self.logger.info(f"Broker configuration {'created' if created else 'updated'} for MetaTrader4")

        except Exception as e:
            self.logger.error(f"Failed to ensure broker configuration: {str(e)}")
            # Don't raise - authentication can still succeed without persistent config

    def _clear_broker_cache(self) -> None:
        """Clear the broker factory cache to pick up updated configuration."""
        try:
            from stonks_overwatch.core.factories.broker_factory import BrokerFactory

            factory = BrokerFactory()
            factory.clear_cache()
            self.logger.debug("Broker factory cache cleared")
        except Exception as e:
            self.logger.error(f"Failed to clear broker cache: {str(e)}")

    def _reconfigure_jobs(self) -> None:
        """
        Trigger job scheduler reconfiguration to pick up newly authenticated broker.

        This ensures the update job is scheduled immediately after authentication.
        """
        try:
            from stonks_overwatch.jobs.jobs_scheduler import JobsScheduler

            if JobsScheduler.scheduler:
                self.logger.info("Reconfiguring job scheduler after MetaTrader4 authentication")
                JobsScheduler._configure_jobs()
                self.logger.info("Job scheduler reconfigured successfully")
            else:
                self.logger.warning("Job scheduler not running, skipping reconfiguration")

        except Exception as e:
            self.logger.error(f"Error reconfiguring job scheduler: {str(e)}")
            # Don't raise exception - authentication succeeded even if job config failed

    def _trigger_portfolio_update(self) -> None:
        """
        Trigger an immediate portfolio update for MetaTrader4.

        This runs the update job immediately after authentication so data is
        available without waiting for the next scheduled update.
        """
        try:
            from stonks_overwatch.jobs.jobs_scheduler import JobsScheduler

            self.logger.info("Triggering immediate MetaTrader4 portfolio update")
            JobsScheduler._update_broker_portfolio(BrokerName.METATRADER4)
            self.logger.info("MetaTrader4 portfolio update completed")

        except Exception as e:
            self.logger.error(f"Error triggering portfolio update: {str(e)}")
            # Don't raise exception - authentication succeeded even if update failed
            # The scheduled job will retry later
