"""
Alpaca authentication service implementation.

Handles API key validation and session management for Alpaca Markets accounts.
"""

from typing import Optional

from django.http import HttpRequest

from stonks_overwatch.config.alpaca import AlpacaConfig
from stonks_overwatch.constants import BrokerName
from stonks_overwatch.core.interfaces.authentication_service import (
    AuthenticationResponse,
    AuthenticationResult,
    AuthenticationServiceInterface,
)
from stonks_overwatch.core.interfaces.base_service import BaseService
from stonks_overwatch.utils.core.logger import StonksLogger
from stonks_overwatch.utils.core.session_keys import SessionKeys


class AlpacaAuthenticationService(BaseService, AuthenticationServiceInterface):
    """
    Authentication service for Alpaca Markets.

    Validates API keys by calling get_account() and stores credentials
    in the Django session and optionally in the database.
    """

    def __init__(self, config: Optional[AlpacaConfig] = None, **kwargs):
        """
        Initialize the Alpaca authentication service.

        Args:
            config: Optional Alpaca configuration (injected by factory if not provided)
            **kwargs: Additional keyword arguments
        """
        super().__init__(config, **kwargs)
        self.logger = StonksLogger.get_logger(__name__, "[ALPACA|AUTH]")

    @property
    def broker_name(self) -> BrokerName:
        """Return the broker name."""
        return BrokerName.ALPACA

    def validate_credentials(self, api_key: str, secret_key: str, paper_trading: bool = False) -> dict:
        """
        Validate Alpaca API credentials by calling the account endpoint.

        Args:
            api_key: Alpaca API key
            secret_key: Alpaca secret key
            paper_trading: Whether to validate against the paper trading API

        Returns:
            Dictionary with 'success' bool, 'message' str, and optional 'account_info'
        """
        try:
            from alpaca.trading.client import TradingClient

            validation_client = TradingClient(
                api_key=api_key,
                secret_key=secret_key,
                paper=paper_trading,
            )
            account = validation_client.get_account()

            if account and account.id:
                mode = "paper" if paper_trading else "live"
                self.logger.info(f"Alpaca credentials validated successfully ({mode} mode)")
                return {
                    "success": True,
                    "message": "Credentials validated successfully",
                    "account_info": {
                        "account_id": str(account.id),
                        "equity": str(account.equity),
                        "cash": str(account.cash),
                        "currency": str(account.currency),
                        "paper_trading": paper_trading,
                    },
                }
            else:
                self.logger.warning("Alpaca credentials validation failed - invalid response")
                return {"success": False, "message": "Invalid API response - please check your credentials"}

        except Exception as e:
            error_msg = str(e).lower()
            if "forbidden" in error_msg or "unauthorized" in error_msg or "invalid" in error_msg:
                self.logger.warning(f"Alpaca credentials validation failed: {e}")
                return {"success": False, "message": "Invalid API credentials - please check your API key and secret"}
            elif "rate limit" in error_msg:
                self.logger.warning(f"Alpaca rate limit exceeded: {e}")
                return {"success": False, "message": "Rate limit exceeded - please try again later"}
            else:
                self.logger.error(f"Alpaca credentials validation error: {e}")
                return {"success": False, "message": f"Connection error: {e}"}

    def authenticate_user(
        self, request: HttpRequest, api_key: str, api_secret: str, remember_me: bool = False, **kwargs
    ) -> dict:
        """
        Authenticate user with Alpaca API credentials.

        Args:
            request: Django HTTP request
            api_key: Alpaca API key
            api_secret: Alpaca secret key
            remember_me: Whether to store credentials persistently in the DB
            **kwargs: Additional arguments (e.g. paper_trading=True)

        Returns:
            Dictionary with authentication result
        """
        paper_trading = kwargs.get("paper_trading", False)
        try:
            validation_result = self.validate_credentials(api_key, api_secret, paper_trading)
            if not validation_result["success"]:
                return validation_result

            request.session[SessionKeys.get_authenticated_key(BrokerName.ALPACA)] = True
            request.session[SessionKeys.get_credentials_key(BrokerName.ALPACA)] = {
                "api_key": api_key,
                "secret_key": api_secret,
                "paper_trading": paper_trading,
            }

            self._ensure_broker_configuration(api_key, api_secret, paper_trading, remember_me)
            self._clear_broker_cache()
            self._reset_alpaca_client()
            self._reconfigure_jobs()
            self._trigger_portfolio_update()

            self.logger.info("Alpaca user authentication successful")
            return {
                "success": True,
                "message": "Authentication successful",
                "account_info": validation_result.get("account_info", {}),
            }

        except Exception as e:
            self.logger.error(f"Alpaca authentication error: {e}")
            return {"success": False, "message": f"Authentication failed: {e}"}

    def is_user_authenticated(self, request: HttpRequest) -> bool:
        """
        Check if the user is authenticated with Alpaca.

        Relies on the session flag set during ``authenticate_user`` rather than
        making a live API call, so it is safe to call on every request without
        introducing latency or triggering rate-limits.

        Args:
            request: Django HTTP request

        Returns:
            True if the authenticated session flag is set and credentials are
            present in the session, False otherwise
        """
        try:
            if not request.session.get(SessionKeys.get_authenticated_key(BrokerName.ALPACA), False):
                return False
            return bool(request.session.get(SessionKeys.get_credentials_key(BrokerName.ALPACA)))
        except Exception as e:
            self.logger.error(f"Authentication check error: {e}")
            return False

    def logout_user(self, request: HttpRequest) -> bool:
        """
        Logout the user from the Alpaca session.

        Args:
            request: Django HTTP request

        Returns:
            True if logout was successful
        """
        try:
            request.session.pop(SessionKeys.get_authenticated_key(BrokerName.ALPACA), None)
            request.session.pop(SessionKeys.get_credentials_key(BrokerName.ALPACA), None)
            self.logger.info("Alpaca user logged out successfully")
            return True
        except Exception as e:
            self.logger.error(f"Logout error: {e}")
            return False

    def _ensure_broker_configuration(
        self, api_key: str, secret_key: str, paper_trading: bool, remember_me: bool
    ) -> None:
        """
        Ensure broker configuration exists in the database after successful authentication.

        Args:
            api_key: Alpaca API key
            secret_key: Alpaca secret key
            paper_trading: Whether paper trading mode is active
            remember_me: Whether to persist credentials
        """
        try:
            from stonks_overwatch.services.brokers.models import BrokersConfiguration

            credentials_to_store = (
                {"api_key": api_key, "secret_key": secret_key, "paper_trading": paper_trading}
                if remember_me
                else {"api_key": "", "secret_key": "", "paper_trading": paper_trading}
            )

            broker_config, created = BrokersConfiguration.objects.get_or_create(
                broker_name=BrokerName.ALPACA,
                defaults={
                    "enabled": True,
                    "start_date": self.config.start_date if self.config else AlpacaConfig.DEFAULT_ALPACA_START_DATE,
                    "update_frequency": self.config.update_frequency_minutes
                    if self.config
                    else AlpacaConfig.DEFAULT_ALPACA_UPDATE_FREQUENCY,
                    "credentials": credentials_to_store,
                },
            )

            if not created:
                broker_config.enabled = True
                if remember_me:
                    broker_config.credentials = credentials_to_store
                broker_config.save()

            action = "created" if created else "updated"
            creds_note = "with credentials" if remember_me else "without credentials"
            self.logger.info(f"Alpaca broker configuration {action} {creds_note}")

        except Exception as e:
            self.logger.error(f"Error ensuring broker configuration: {e}")

    def _clear_broker_cache(self) -> None:
        """Clear the broker factory cache so new configuration is picked up."""
        try:
            from stonks_overwatch.core.factories.broker_factory import BrokerFactory

            BrokerFactory().clear_cache()
            self.logger.debug("Cleared broker factory cache")
        except Exception as e:
            self.logger.error(f"Error clearing broker factory cache: {e}")

    def _reset_alpaca_client(self) -> None:
        """Reset the AlpacaClient singleton so it reinitializes with new credentials."""
        try:
            from stonks_overwatch.services.brokers.alpaca.client.alpaca_client import AlpacaClient
            from stonks_overwatch.utils.core.singleton import reset_singleton

            reset_singleton(AlpacaClient)
            self.logger.debug("Reset AlpacaClient singleton")
        except Exception as e:
            self.logger.error(f"Error resetting AlpacaClient singleton: {e}")

    def _reconfigure_jobs(self) -> None:
        """Trigger job scheduler reconfiguration to include the newly authenticated broker."""
        try:
            from stonks_overwatch.jobs.jobs_scheduler import JobsScheduler

            if JobsScheduler.scheduler:
                JobsScheduler._configure_jobs()
                self.logger.info("Job scheduler reconfigured after Alpaca authentication")
        except Exception as e:
            self.logger.error(f"Error reconfiguring job scheduler: {e}")

    def _trigger_portfolio_update(self) -> None:
        """Trigger an immediate portfolio update so data is available right away."""
        try:
            from stonks_overwatch.jobs.jobs_scheduler import JobsScheduler

            self.logger.info("Triggering immediate Alpaca portfolio update")
            JobsScheduler._update_broker_portfolio(BrokerName.ALPACA)
            self.logger.info("Alpaca portfolio update triggered")
        except Exception as e:
            self.logger.error(f"Error triggering portfolio update: {e}")

    # --- AuthenticationServiceInterface methods not applicable to Alpaca ---

    def check_broker_connection(self, request: HttpRequest) -> AuthenticationResponse:
        """Not applicable for Alpaca (API key auth only)."""
        return AuthenticationResponse(
            result=AuthenticationResult.CONFIGURATION_ERROR,
            message="Broker connection check is not applicable for Alpaca",
        )

    def handle_totp_authentication(self, request: HttpRequest, one_time_password: int) -> AuthenticationResponse:
        """Not applicable for Alpaca (no TOTP required)."""
        return AuthenticationResponse(
            result=AuthenticationResult.CONFIGURATION_ERROR,
            message="TOTP authentication is not applicable for Alpaca",
        )

    def handle_in_app_authentication(self, request: HttpRequest) -> AuthenticationResponse:
        """Not applicable for Alpaca (no in-app auth required)."""
        return AuthenticationResponse(
            result=AuthenticationResult.CONFIGURATION_ERROR,
            message="In-app authentication is not applicable for Alpaca",
        )

    def is_broker_enabled(self) -> bool:
        """Check if Alpaca is enabled in the configuration."""
        try:
            from stonks_overwatch.core.factories.broker_factory import BrokerFactory

            config = BrokerFactory().create_config(self.broker_name)
            return config is not None and config.is_enabled()
        except Exception as e:
            self.logger.error(f"Error checking if Alpaca is enabled: {e}")
            return False

    def is_offline_mode(self) -> bool:
        """Check if offline mode is active."""
        try:
            return self.config.offline_mode if self.config else False
        except Exception:
            return False

    def is_maintenance_mode_allowed(self) -> bool:
        """Alpaca does not have a maintenance mode."""
        return False

    def should_check_connection(self, request: HttpRequest) -> bool:
        """Alpaca does not require periodic connection checks."""
        return False

    def get_authentication_status(self, request: HttpRequest) -> dict:
        """Return authentication status information."""
        try:
            return {
                "broker": BrokerName.ALPACA.value,
                "is_authenticated": self.is_user_authenticated(request),
                "offline_mode": self.is_offline_mode(),
                "has_credentials": request.session.get(SessionKeys.get_credentials_key(BrokerName.ALPACA)) is not None,
            }
        except Exception as e:
            self.logger.error(f"Error getting authentication status: {e}")
            return {"broker": BrokerName.ALPACA.value, "error": str(e)}

    def handle_authentication_error(
        self, request: HttpRequest, error: Exception, credentials=None
    ) -> AuthenticationResponse:
        """
        Handle authentication errors.

        Args:
            request: HTTP request
            error: The exception that occurred
            credentials: Optional credentials (not used for Alpaca)

        Returns:
            AuthenticationResponse with error details
        """
        error_msg = str(error).lower()
        if "forbidden" in error_msg or "unauthorized" in error_msg or "invalid" in error_msg:
            return AuthenticationResponse(
                result=AuthenticationResult.INVALID_CREDENTIALS,
                message="Invalid API credentials",
            )
        elif "rate limit" in error_msg:
            return AuthenticationResponse(
                result=AuthenticationResult.CONNECTION_ERROR,
                message="Rate limit exceeded",
            )
        else:
            return AuthenticationResponse(
                result=AuthenticationResult.CONNECTION_ERROR,
                message=f"Authentication error: {error}",
            )
