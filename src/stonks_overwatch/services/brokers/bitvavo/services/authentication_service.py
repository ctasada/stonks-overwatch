"""
Bitvavo authentication service implementation.

This module provides authentication functionality specific to Bitvavo,
handling API key validation and connection testing.
"""

from typing import Optional

from django.http import HttpRequest

from stonks_overwatch.config.bitvavo import BitvavoConfig
from stonks_overwatch.core.interfaces.base_service import BaseService
from stonks_overwatch.utils.core.logger import StonksLogger


class BitvavoAuthenticationService(BaseService):
    """
    Authentication service for Bitvavo.

    Handles API key validation and connection testing for Bitvavo accounts.
    """

    BROKER_NAME = "bitvavo"

    def __init__(self, config: Optional[BitvavoConfig] = None, **kwargs):
        """
        Initialize the Bitvavo authentication service.

        Args:
            config: Optional Bitvavo configuration (injected by factory if not provided)
            **kwargs: Additional keyword arguments
        """
        super().__init__(config, **kwargs)
        self.logger = StonksLogger.get_logger(__name__, "[BITVAVO|AUTH]")

    @property
    def broker_name(self) -> str:
        """Return the broker name."""
        return self.BROKER_NAME

    def validate_credentials(self, api_key: str, api_secret: str) -> dict:
        """
        Validate Bitvavo API credentials.

        Args:
            api_key: Bitvavo API key
            api_secret: Bitvavo API secret

        Returns:
            Dictionary with validation result and message
        """
        try:
            # Create Bitvavo client for credential validation
            # We bypass BitvavoService singleton to avoid interference with existing sessions
            from python_bitvavo_api.bitvavo import Bitvavo

            validation_client = Bitvavo(
                {
                    "APIKEY": api_key,
                    "APISECRET": api_secret,
                    "debugging": False,
                }
            )

            # Test API call to validate credentials
            account_info = validation_client.account()

            if account_info and "fees" in account_info:
                self.logger.info("Bitvavo credentials validated successfully")
                return {
                    "success": True,
                    "message": "Credentials validated successfully",
                    "account_info": {
                        "fees": account_info.get("fees", {}),
                        "remaining_limit": validation_client.getRemainingLimit(),
                    },
                }
            else:
                self.logger.warning("Bitvavo credentials validation failed - invalid response")
                return {"success": False, "message": "Invalid API response - please check your credentials"}

        except Exception as e:
            error_msg = str(e).lower()

            if "unauthorized" in error_msg or "invalid" in error_msg:
                self.logger.warning(f"Bitvavo credentials validation failed: {str(e)}")
                return {"success": False, "message": "Invalid API credentials - please check your API key and secret"}
            elif "rate limit" in error_msg:
                self.logger.warning(f"Bitvavo rate limit exceeded: {str(e)}")
                return {"success": False, "message": "Rate limit exceeded - please try again later"}
            else:
                self.logger.error(f"Bitvavo credentials validation error: {str(e)}")
                return {"success": False, "message": f"Connection error: {str(e)}"}

    def authenticate_user(self, request: HttpRequest, api_key: str, api_secret: str, remember_me: bool = False) -> dict:
        """
        Authenticate user with Bitvavo API credentials.

        Args:
            request: Django HTTP request
            api_key: Bitvavo API key
            api_secret: Bitvavo API secret
            remember_me: Whether to store credentials for future sessions

        Returns:
            Dictionary with authentication result
        """
        try:
            # Validate credentials first
            validation_result = self.validate_credentials(api_key, api_secret)

            if not validation_result["success"]:
                return validation_result

            # Store credentials in session
            request.session["bitvavo_authenticated"] = True
            request.session["bitvavo_credentials"] = {
                "apikey": api_key,
                "apisecret": api_secret,
            }

            # Always ensure broker configuration exists after successful authentication
            # This is needed for dashboard and other services to work properly
            self._ensure_broker_configuration(api_key, api_secret, remember_me)

            # Clear the broker factory cache so it picks up the updated configuration
            self._clear_broker_cache()

            # Reset the Bitvavo client singleton so it reinitializes with new credentials
            self._reset_bitvavo_client()

            # Trigger job scheduler reconfiguration to pick up the new broker
            self._reconfigure_jobs()

            # Trigger immediate portfolio update so data is available right away
            self._trigger_portfolio_update()

            self.logger.info("Bitvavo user authentication successful")
            return {
                "success": True,
                "message": "Authentication successful",
                "account_info": validation_result.get("account_info", {}),
            }

        except Exception as e:
            self.logger.error(f"Bitvavo authentication error: {str(e)}")
            return {"success": False, "message": f"Authentication failed: {str(e)}"}

    def is_user_authenticated(self, request: HttpRequest) -> bool:
        """
        Check if user is authenticated with Bitvavo.

        Args:
            request: Django HTTP request

        Returns:
            True if authenticated, False otherwise
        """
        try:
            # Check session authentication
            if not request.session.get("bitvavo_authenticated", False):
                return False

            # Verify credentials are still valid
            credentials = request.session.get("bitvavo_credentials")
            if not credentials:
                return False

            # Quick validation check
            validation_result = self.validate_credentials(credentials["apikey"], credentials["apisecret"])

            return validation_result["success"]

        except Exception as e:
            self.logger.error(f"Authentication check error: {str(e)}")
            return False

    def logout_user(self, request: HttpRequest) -> bool:
        """
        Logout user from Bitvavo session.

        Args:
            request: Django HTTP request

        Returns:
            True if logout successful
        """
        try:
            # Clear session data
            request.session.pop("bitvavo_authenticated", None)
            request.session.pop("bitvavo_credentials", None)
            request.session.pop("bitvavo_totp_required", None)
            request.session.pop("bitvavo_in_app_auth_required", None)

            self.logger.info("Bitvavo user logged out successfully")
            return True

        except Exception as e:
            self.logger.error(f"Logout error: {str(e)}")
            return False

    def _ensure_broker_configuration(self, api_key: str, api_secret: str, remember_me: bool) -> None:
        """
        Ensure broker configuration exists in database after successful authentication.

        This method always creates or updates the broker configuration to ensure
        the dashboard and other services can work properly, regardless of remember_me setting.

        Args:
            api_key: Bitvavo API key
            api_secret: Bitvavo API secret
            remember_me: Whether to store credentials permanently
        """
        try:
            from stonks_overwatch.services.brokers.models import BrokersConfiguration

            # Get or create broker configuration
            broker_config, created = BrokersConfiguration.objects.get_or_create(
                broker_name=self.BROKER_NAME,
                defaults={
                    "enabled": True,
                    "start_date": self.config.start_date if self.config else BitvavoConfig.DEFAULT_BITVAVO_START_DATE,
                    "update_frequency": self.config.update_frequency_minutes
                    if self.config
                    else BitvavoConfig.DEFAULT_BITVAVO_UPDATE_FREQUENCY,
                    "credentials": {
                        "apikey": api_key if remember_me else "",
                        "apisecret": api_secret if remember_me else "",
                    },
                },
            )

            if not created:
                # Update existing configuration
                broker_config.enabled = True
                # Only update credentials if remember_me is True
                if remember_me:
                    broker_config.credentials = {
                        "apikey": api_key,
                        "apisecret": api_secret,
                    }
                broker_config.save()

            action = "created" if created else "updated"
            credentials_stored = "with credentials" if remember_me else "without credentials"
            self.logger.info(f"Bitvavo broker configuration {action} {credentials_stored}")

        except Exception as e:
            self.logger.error(f"Error ensuring broker configuration: {str(e)}")
            # Don't raise exception - authentication can still succeed without storing

    def _store_credentials(self, api_key: str, api_secret: str) -> None:
        """
        Store encrypted credentials in database (legacy method - use _ensure_broker_configuration instead).

        .. deprecated::
            Use _ensure_broker_configuration instead. This method will be removed in a future version.

        Args:
            api_key: Bitvavo API key
            api_secret: Bitvavo API secret
        """
        import warnings

        warnings.warn(
            "_store_credentials is deprecated, use _ensure_broker_configuration instead",
            DeprecationWarning,
            stacklevel=2,
        )
        # Delegate to the new method with remember_me=True
        self._ensure_broker_configuration(api_key, api_secret, remember_me=True)

    def _clear_broker_cache(self) -> None:
        """
        Clear the broker factory cache for ALL brokers.

        This ensures that the factory will reload all configurations from the database
        after authentication. We clear all brokers (not just Bitvavo) because the
        configuration endpoint needs to see the current state of all brokers.
        """
        try:
            from stonks_overwatch.core.factories.broker_factory import BrokerFactory

            broker_factory = BrokerFactory()
            # Clear cache for ALL brokers to ensure configuration endpoint shows correct state
            broker_factory.clear_cache()  # No broker_name = clear all caches
            self.logger.debug("Cleared broker factory cache for all brokers")

        except Exception as e:
            self.logger.error(f"Error clearing broker factory cache: {str(e)}")
            # Don't raise exception - authentication succeeded even if cache clear failed

    def _reset_bitvavo_client(self) -> None:
        """
        Reset the BitvavoService singleton so it reinitializes with new credentials.

        The BitvavoService is a singleton that initializes its client in __init__.
        After authentication, we need to reset the singleton so it picks up the
        new credentials from the updated configuration.
        """
        try:
            from stonks_overwatch.services.brokers.bitvavo.client.bitvavo_client import BitvavoService
            from stonks_overwatch.utils.core.singleton import reset_singleton

            # Reset the singleton to force reinitialization with new credentials
            reset_singleton(BitvavoService)
            self.logger.debug("Reset BitvavoService singleton")

        except Exception as e:
            self.logger.error(f"Error resetting BitvavoService singleton: {str(e)}")
            # Don't raise exception - authentication succeeded even if reset failed

    def _reconfigure_jobs(self) -> None:
        """
        Trigger job scheduler reconfiguration to pick up newly authenticated broker.

        This ensures the update job is scheduled immediately after authentication.
        """
        try:
            from stonks_overwatch.jobs.jobs_scheduler import JobsScheduler

            if JobsScheduler.scheduler:
                self.logger.info("Reconfiguring job scheduler after authentication")
                JobsScheduler._configure_jobs()
                self.logger.info("Job scheduler reconfigured successfully")
            else:
                self.logger.warning("Job scheduler not running, skipping reconfiguration")

        except Exception as e:
            self.logger.error(f"Error reconfiguring job scheduler: {str(e)}")
            # Don't raise exception - authentication succeeded even if job config failed

    def _trigger_portfolio_update(self) -> None:
        """
        Trigger an immediate portfolio update for Bitvavo.

        This runs the update job immediately after authentication so data is
        available without waiting for the next scheduled update.
        """
        try:
            from stonks_overwatch.jobs.jobs_scheduler import JobsScheduler

            self.logger.info("Triggering immediate Bitvavo portfolio update")
            JobsScheduler._update_broker_portfolio(self.BROKER_NAME)
            self.logger.info("Bitvavo portfolio update completed")

        except Exception as e:
            self.logger.error(f"Error triggering portfolio update: {str(e)}")
            # Don't raise exception - authentication succeeded even if update failed
            # The scheduled job will retry later
