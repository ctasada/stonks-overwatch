"""Configuration classes for Alpaca Markets broker integration."""

from dataclasses import dataclass
from datetime import date
from typing import Any, Dict, Optional

from stonks_overwatch.config.base_config import BaseConfig
from stonks_overwatch.config.base_credentials import BaseCredentials
from stonks_overwatch.constants import BrokerName
from stonks_overwatch.utils.core.localization import LocalizationUtility
from stonks_overwatch.utils.core.session_keys import SessionKeys


@dataclass
class AlpacaCredentials(BaseCredentials):
    """Credentials for Alpaca Markets API authentication."""

    api_key: str
    secret_key: str
    paper_trading: bool = False

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "AlpacaCredentials":
        """
        Create credentials from a dictionary.

        Args:
            data: Dictionary containing credential fields

        Returns:
            AlpacaCredentials instance
        """
        if not data:
            return cls("", "")
        return cls(
            api_key=data.get("api_key", ""),
            secret_key=data.get("secret_key", ""),
            paper_trading=data.get("paper_trading", False),
        )

    @classmethod
    def from_request(cls, request) -> "AlpacaCredentials":
        """
        Create credentials from Django request session.

        Args:
            request: Django HTTP request

        Returns:
            AlpacaCredentials from session data
        """
        session_credentials = request.session.get(SessionKeys.get_credentials_key(BrokerName.ALPACA), {})
        return cls.from_dict(session_credentials)

    def has_minimal_credentials(self) -> bool:
        """
        Check if minimal credentials are provided.

        Returns:
            True if both api_key and secret_key are present
        """
        return bool(self.api_key and self.secret_key)

    def to_auth_params(self) -> dict:
        """
        Convert credentials to authentication parameters.

        Returns:
            Dictionary with authentication parameters for Alpaca auth service

        Note:
            remember_me is intentionally omitted as this method is used for
            auto-authentication with already-stored credentials.
        """
        return {
            "api_key": self.api_key,
            "secret_key": self.secret_key,
            "paper_trading": self.paper_trading,
        }


class AlpacaConfig(BaseConfig):
    """Configuration for Alpaca Markets broker."""

    config_key = BrokerName.ALPACA.value
    DEFAULT_ALPACA_UPDATE_FREQUENCY = 15
    DEFAULT_ALPACA_START_DATE_STR = "2020-01-01"
    DEFAULT_ALPACA_START_DATE = LocalizationUtility.convert_string_to_date(DEFAULT_ALPACA_START_DATE_STR)

    def __init__(
        self,
        credentials: Optional[AlpacaCredentials],
        start_date: date,
        update_frequency_minutes: int = DEFAULT_ALPACA_UPDATE_FREQUENCY,
        enabled: bool = False,
        offline_mode: bool = None,
    ) -> None:
        """
        Initialize AlpacaConfig.

        Args:
            credentials: Alpaca API credentials
            start_date: Start date for fetching historical data
            update_frequency_minutes: How often to sync data (in minutes)
            enabled: Whether this broker is enabled
            offline_mode: Whether to run in offline mode (defaults to demo mode check)
        """
        if offline_mode is None:
            from stonks_overwatch.utils.core.demo_mode import is_demo_mode

            offline_mode = is_demo_mode()

        self.logger.info(f"Initializing AlpacaConfig with offline_mode={offline_mode}")
        super().__init__(credentials, start_date, enabled, offline_mode, update_frequency_minutes)

    def __eq__(self, value: object) -> bool:
        if isinstance(value, AlpacaConfig):
            return super().__eq__(value)
        return False

    def __repr__(self) -> str:
        return (
            f"AlpacaConfig(enabled={self.enabled}, "
            f"offline_mode={self.offline_mode}, "
            f"credentials={self.credentials}, "
            f"start_date={self.start_date}, "
            f"update_frequency_minutes={self.update_frequency_minutes})"
        )

    @property
    def get_credentials(self) -> Optional[AlpacaCredentials]:
        """Return Alpaca credentials."""
        return self.credentials

    @property
    def paper_trading(self) -> bool:
        """Return whether paper trading mode is enabled."""
        if self.credentials and isinstance(self.credentials, AlpacaCredentials):
            return self.credentials.paper_trading
        return False

    @classmethod
    def from_dict(cls, data: dict) -> "AlpacaConfig":
        """
        Create AlpacaConfig from a dictionary.

        Args:
            data: Configuration dictionary

        Returns:
            AlpacaConfig instance
        """
        enabled = data.get("enabled", False)
        credentials_data = data.get("credentials")
        credentials = AlpacaCredentials.from_dict(credentials_data) if credentials_data else None
        start_date = data.get("start_date", cls.DEFAULT_ALPACA_START_DATE)
        if isinstance(start_date, str):
            start_date = LocalizationUtility.convert_string_to_date(start_date)
        update_frequency_minutes = data.get("update_frequency_minutes", cls.DEFAULT_ALPACA_UPDATE_FREQUENCY)

        from stonks_overwatch.utils.core.demo_mode import is_demo_mode

        demo_mode = is_demo_mode()
        if demo_mode:
            offline_mode = True
        else:
            offline_mode = data.get("offline_mode") if "offline_mode" in data else None

        return cls(credentials, start_date, update_frequency_minutes, enabled, offline_mode)

    @classmethod
    def default(cls) -> "AlpacaConfig":
        """
        Create default AlpacaConfig.

        Returns:
            Default AlpacaConfig instance loaded from DB/JSON or with default values
        """
        try:
            return cls.from_db_with_json_override(BrokerName.ALPACA)
        except Exception as e:
            cls.logger.debug(f"Cannot load ALPACA configuration ({e}), using defaults", exc_info=True)
            return AlpacaConfig(
                credentials=None,
                start_date=cls.DEFAULT_ALPACA_START_DATE,
                update_frequency_minutes=cls.DEFAULT_ALPACA_UPDATE_FREQUENCY,
            )
