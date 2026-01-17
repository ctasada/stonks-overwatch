"""
IBKR authentication service implementation.

This module provides authentication functionality specific to Interactive Brokers,
handling OAuth token validation and connection testing.
"""

from typing import Optional

from django.http import HttpRequest

from stonks_overwatch.config.ibkr import IbkrConfig, IbkrCredentials
from stonks_overwatch.constants import BrokerName
from stonks_overwatch.core.interfaces.authentication_service import (
    AuthenticationResponse,
    AuthenticationResult,
    AuthenticationServiceInterface,
)
from stonks_overwatch.core.interfaces.base_service import BaseService
from stonks_overwatch.utils.core.logger import StonksLogger
from stonks_overwatch.utils.core.session_keys import SessionKeys


class IbkrAuthenticationService(BaseService, AuthenticationServiceInterface):
    """
    Authentication service for Interactive Brokers.

    Handles OAuth token validation and connection testing for IBKR accounts.
    """

    def __init__(self, config: Optional[IbkrConfig] = None, **kwargs):
        """
        Initialize the IBKR authentication service.

        Args:
            config: Optional IBKR configuration (injected by factory if not provided)
            **kwargs: Additional keyword arguments
        """
        super().__init__(config, **kwargs)
        self.logger = StonksLogger.get_logger(__name__, "[IBKR|AUTH]")

    @property
    def broker_name(self) -> BrokerName:
        """Return the broker name."""
        return BrokerName.IBKR

    def validate_credentials(
        self,
        access_token: str,
        access_token_secret: str,
        consumer_key: str,
        dh_prime: str,
        encryption_key: Optional[str] = None,
        signature_key: Optional[str] = None,
    ) -> dict:
        """
        Validate IBKR OAuth credentials.

        Args:
            access_token: IBKR OAuth access token
            access_token_secret: IBKR OAuth access token secret
            consumer_key: IBKR OAuth consumer key
            dh_prime: IBKR Diffie-Hellman prime
            encryption_key: Optional encryption key content
            signature_key: Optional signature key content

        Returns:
            Dictionary with validation result and message
        """
        try:
            # Basic validation of required fields
            if not all([access_token, access_token_secret, consumer_key, dh_prime]):
                return {
                    "success": False,
                    "message": (
                        "Missing required OAuth credentials (access_token, access_token_secret, consumer_key, dh_prime)"
                    ),
                }

            # Validate token format (basic checks)
            if len(access_token) < 10 or len(access_token_secret) < 10:
                return {"success": False, "message": "Invalid token format - tokens too short"}

            if len(consumer_key) < 5:
                return {"success": False, "message": "Invalid consumer key format"}

            # TODO: Implement actual IBKR API validation
            # For now, we'll do basic format validation
            # In a real implementation, you would:
            # 1. Create IBKR client with OAuth credentials
            # 2. Make a test API call (e.g., get account info)
            # 3. Validate the response

            self.logger.info("IBKR credentials validated successfully (placeholder implementation)")
            return {
                "success": True,
                "message": "Credentials validated successfully",
                "account_info": {
                    "consumer_key": consumer_key[:8] + "...",  # Masked for security
                    "validation_method": "format_check",  # Indicates this is placeholder
                },
            }

        except Exception as e:
            error_msg = str(e).lower()

            if "unauthorized" in error_msg or "invalid" in error_msg:
                self.logger.warning(f"IBKR credentials validation failed: {str(e)}")
                return {"success": False, "message": "Invalid OAuth credentials - please check your tokens"}
            elif "rate limit" in error_msg:
                self.logger.warning(f"IBKR rate limit exceeded: {str(e)}")
                return {"success": False, "message": "Rate limit exceeded - please try again later"}
            else:
                self.logger.error(f"IBKR credentials validation error: {str(e)}")
                return {"success": False, "message": f"Connection error: {str(e)}"}

    def authenticate_user(
        self,
        request: HttpRequest,
        access_token: str,
        access_token_secret: str,
        consumer_key: str,
        dh_prime: str,
        encryption_key: Optional[str] = None,
        signature_key: Optional[str] = None,
        remember_me: bool = False,
    ) -> dict:
        """
        Authenticate user with IBKR OAuth credentials.

        Args:
            request: Django HTTP request
            access_token: IBKR OAuth access token
            access_token_secret: IBKR OAuth access token secret
            consumer_key: IBKR OAuth consumer key
            dh_prime: IBKR Diffie-Hellman prime
            encryption_key: Optional encryption key content
            signature_key: Optional signature key content
            remember_me: Whether to store credentials for future sessions

        Returns:
            Dictionary with authentication result
        """
        try:
            # Validate credentials first
            validation_result = self.validate_credentials(
                access_token, access_token_secret, consumer_key, dh_prime, encryption_key, signature_key
            )

            if not validation_result["success"]:
                return validation_result

            # Store credentials in session
            request.session[SessionKeys.get_authenticated_key(BrokerName.IBKR.value)] = True
            request.session[SessionKeys.get_credentials_key(BrokerName.IBKR.value)] = {
                "access_token": access_token,
                "access_token_secret": access_token_secret,
                "consumer_key": consumer_key,
                "dh_prime": dh_prime,
                "encryption_key": encryption_key,
                "signature_key": signature_key,
            }

            # Always ensure broker configuration exists after successful authentication
            self._ensure_broker_configuration(
                access_token, access_token_secret, consumer_key, dh_prime, encryption_key, signature_key, remember_me
            )

            # Clear the broker factory cache so it picks up the updated configuration
            self._clear_broker_cache()

            # Reset any IBKR client singletons
            self._reset_ibkr_client()

            # Trigger job scheduler reconfiguration to pick up the new broker
            self._reconfigure_jobs()

            # Trigger immediate portfolio update so data is available right away
            self._trigger_portfolio_update()

            self.logger.info("IBKR user authentication successful")
            return {
                "success": True,
                "message": "Authentication successful",
                "account_info": validation_result.get("account_info", {}),
            }

        except Exception as e:
            self.logger.error(f"IBKR authentication error: {str(e)}")
            return {"success": False, "message": f"Authentication failed: {str(e)}"}

    def is_user_authenticated(self, request: HttpRequest) -> bool:
        """
        Check if user is authenticated with IBKR.

        Args:
            request: Django HTTP request

        Returns:
            True if authenticated, False otherwise
        """
        try:
            # Check session authentication
            if not request.session.get(SessionKeys.get_authenticated_key(BrokerName.IBKR.value), False):
                return False

            # Verify credentials are still valid
            credentials = request.session.get(SessionKeys.get_credentials_key(BrokerName.IBKR.value))
            if not credentials:
                return False

            # Quick validation check
            validation_result = self.validate_credentials(
                credentials.get("access_token", ""),
                credentials.get("access_token_secret", ""),
                credentials.get("consumer_key", ""),
                credentials.get("dh_prime", ""),
                credentials.get("encryption_key"),
                credentials.get("signature_key"),
            )

            return validation_result["success"]

        except Exception as e:
            self.logger.error(f"Authentication check error: {str(e)}")
            return False

    def logout_user(self, request: HttpRequest) -> bool:
        """
        Logout user from IBKR session.

        Args:
            request: Django HTTP request

        Returns:
            True if logout successful
        """
        try:
            # Clear session data
            request.session.pop(SessionKeys.get_authenticated_key(BrokerName.IBKR.value), None)
            request.session.pop(SessionKeys.get_credentials_key(BrokerName.IBKR.value), None)
            request.session.pop(SessionKeys.get_totp_required_key(BrokerName.IBKR.value), None)
            request.session.pop(SessionKeys.get_in_app_auth_required_key(BrokerName.IBKR.value), None)

            self.logger.info("IBKR user logged out successfully")
            return True

        except Exception as e:
            self.logger.error(f"IBKR logout error: {str(e)}")
            return False

    # Implementation of AuthenticationServiceInterface methods
    def check_degiro_connection(self, request: HttpRequest) -> AuthenticationResponse:
        """
        Check connection - not applicable for IBKR.

        Args:
            request: Django HTTP request

        Returns:
            AuthenticationResponse indicating this is not applicable
        """
        return AuthenticationResponse(
            result=AuthenticationResult.CONFIGURATION_ERROR,
            message="DeGiro connection check not applicable for IBKR broker",
        )

    def handle_totp_authentication(self, request: HttpRequest, one_time_password: int) -> AuthenticationResponse:
        """
        Handle TOTP authentication - not currently supported for IBKR.

        Args:
            request: Django HTTP request
            one_time_password: The 2FA code

        Returns:
            AuthenticationResponse indicating TOTP is not supported
        """
        return AuthenticationResponse(
            result=AuthenticationResult.CONFIGURATION_ERROR,
            message="TOTP authentication not supported for IBKR broker",
        )

    def handle_in_app_authentication(self, request: HttpRequest) -> AuthenticationResponse:
        """
        Handle in-app authentication - not currently supported for IBKR.

        Args:
            request: Django HTTP request

        Returns:
            AuthenticationResponse indicating in-app auth is not supported
        """
        return AuthenticationResponse(
            result=AuthenticationResult.CONFIGURATION_ERROR,
            message="In-app authentication not supported for IBKR broker",
        )

    def is_broker_enabled(self) -> bool:
        """
        Check if the broker authentication is enabled in the configuration.

        Returns:
            bool: True if IBKR is enabled, False otherwise
        """
        try:
            from stonks_overwatch.core.factories.broker_factory import BrokerFactory

            broker_factory = BrokerFactory()
            config = broker_factory.create_config(self.broker_name)

            return config is not None and config.is_enabled()

        except Exception as e:
            self.logger.error(f"Error checking if {self.broker_name} is enabled: {str(e)}")
            return False

    def is_offline_mode(self) -> bool:
        """
        Check if IBKR is in offline mode.

        Returns:
            True if offline mode is enabled, False otherwise
        """
        return self.config.offline_mode if self.config else False

    def is_maintenance_mode_allowed(self) -> bool:
        """
        Check if access is allowed during maintenance mode.

        Returns:
            True if stored credentials are available, False otherwise
        """
        # TODO: Implement stored credentials check
        return False

    def should_check_connection(self, request: HttpRequest) -> bool:
        """
        Determine if a connection check should be performed.

        Args:
            request: Django HTTP request

        Returns:
            True if connection should be checked, False otherwise
        """
        # For IBKR, we check connection if user is authenticated
        return self.is_user_authenticated(request)

    def get_authentication_status(self, request: HttpRequest) -> dict:
        """
        Get comprehensive authentication status for debugging/monitoring.

        Args:
            request: Django HTTP request

        Returns:
            Dictionary containing authentication status information
        """
        try:
            is_authenticated = self.is_user_authenticated(request)
            credentials = request.session.get(SessionKeys.get_credentials_key(BrokerName.IBKR.value))

            return {
                "broker": BrokerName.IBKR,
                "is_authenticated": is_authenticated,
                "has_session_credentials": bool(credentials),
                "has_consumer_key": bool(credentials and credentials.get("consumer_key")) if credentials else False,
                "offline_mode": self.is_offline_mode(),
                "config_enabled": self.config.enabled if self.config else False,
            }

        except Exception as e:
            self.logger.error(f"Error getting authentication status: {str(e)}")
            return {
                "broker": BrokerName.IBKR,
                "is_authenticated": False,
                "error": str(e),
            }

    def handle_authentication_error(
        self, request: HttpRequest, error: Exception, credentials: Optional[IbkrCredentials] = None
    ) -> AuthenticationResponse:
        """
        Handle authentication errors and convert them to appropriate responses.

        Args:
            request: Django HTTP request
            error: The exception that occurred
            credentials: Optional credentials that were being used

        Returns:
            AuthenticationResponse with appropriate error handling
        """
        error_msg = str(error).lower()

        if "unauthorized" in error_msg or "invalid" in error_msg:
            return AuthenticationResponse(
                result=AuthenticationResult.INVALID_CREDENTIALS,
                message="Invalid OAuth credentials - please check your tokens",
            )
        elif "rate limit" in error_msg:
            return AuthenticationResponse(
                result=AuthenticationResult.CONNECTION_ERROR,
                message="Rate limit exceeded - please try again later",
            )
        elif "connection" in error_msg or "network" in error_msg:
            return AuthenticationResponse(
                result=AuthenticationResult.CONNECTION_ERROR,
                message="Connection error - please check your internet connection",
            )
        else:
            self.logger.error(f"Unexpected authentication error: {str(error)}")
            return AuthenticationResponse(
                result=AuthenticationResult.UNKNOWN_ERROR,
                message="An unexpected error occurred during authentication",
            )

    # Helper methods for configuration management
    def _ensure_broker_configuration(
        self,
        access_token: str,
        access_token_secret: str,
        consumer_key: str,
        dh_prime: str,
        encryption_key: Optional[str],
        signature_key: Optional[str],
        remember_me: bool,
    ) -> None:
        """
        Ensure broker configuration exists with the provided credentials.

        Args:
            access_token: IBKR OAuth access token
            access_token_secret: IBKR OAuth access token secret
            consumer_key: IBKR OAuth consumer key
            dh_prime: IBKR Diffie-Hellman prime
            encryption_key: Optional encryption key content
            signature_key: Optional signature key content
            remember_me: Whether to store credentials persistently
        """
        try:
            from stonks_overwatch.services.brokers.models import BrokersConfiguration

            # Get or create broker configuration
            broker_config, created = BrokersConfiguration.objects.get_or_create(
                broker_name=BrokerName.IBKR,
                defaults={
                    "enabled": True,
                    "start_date": self.config.start_date if self.config else None,
                    "update_frequency": self.config.update_frequency_minutes if self.config else 60,
                    "credentials": {
                        "access_token": access_token if remember_me else "",
                        "access_token_secret": access_token_secret if remember_me else "",
                        "consumer_key": consumer_key if remember_me else "",
                        "dh_prime": dh_prime if remember_me else "",
                        "encryption_key": encryption_key if remember_me and encryption_key else "",
                        "signature_key": signature_key if remember_me and signature_key else "",
                    },
                },
            )

            if not created:
                # Update existing configuration
                broker_config.enabled = True
                # Only update credentials if remember_me is True
                if remember_me:
                    broker_config.credentials = {
                        "access_token": access_token,
                        "access_token_secret": access_token_secret,
                        "consumer_key": consumer_key,
                        "dh_prime": dh_prime,
                        "encryption_key": encryption_key or "",
                        "signature_key": signature_key or "",
                    }
                broker_config.save()

            action = "created" if created else "updated"
            credentials_stored = "with credentials" if remember_me else "without credentials"
            self.logger.info(f"IBKR broker configuration {action} {credentials_stored}")

        except Exception as e:
            self.logger.error(f"Error ensuring IBKR configuration: {str(e)}")
            # Don't raise exception - authentication can still succeed without storing

    def _clear_broker_cache(self) -> None:
        """Clear broker factory cache."""
        try:
            from stonks_overwatch.core.factories.broker_factory import BrokerFactory

            factory = BrokerFactory()
            factory.clear_cache()
            self.logger.debug("Cleared broker factory cache")

        except Exception as e:
            self.logger.error(f"Error clearing broker cache: {str(e)}")

    def _reset_ibkr_client(self) -> None:
        """Reset IBKR client singletons."""
        try:
            from stonks_overwatch.services.brokers.ibkr.client.ibkr_service import IbkrService
            from stonks_overwatch.utils.core.singleton import reset_singleton

            reset_singleton(IbkrService)
            self.logger.debug("IBKR client singleton reset successfully")

        except Exception as e:
            self.logger.error(f"Error resetting IBKR client: {str(e)}")

    def _reconfigure_jobs(self) -> None:
        """Reconfigure job scheduler."""
        try:
            from stonks_overwatch.jobs.jobs_scheduler import JobsScheduler

            if JobsScheduler.scheduler:
                JobsScheduler._configure_jobs()
                self.logger.debug("Reconfigured job scheduler")

        except Exception as e:
            self.logger.error(f"Error reconfiguring jobs: {str(e)}")

    def _trigger_portfolio_update(self) -> None:
        """Trigger immediate portfolio update."""
        try:
            from stonks_overwatch.jobs.jobs_scheduler import JobsScheduler

            JobsScheduler._update_broker_portfolio(BrokerName.IBKR)
            self.logger.debug("Triggered IBKR portfolio update")

        except Exception as e:
            self.logger.error(f"Error triggering portfolio update: {str(e)}")
