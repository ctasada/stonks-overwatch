from dataclasses import dataclass
from datetime import date
from typing import Any, Dict, Optional

from stonks_overwatch.config.base_config import BaseConfig
from stonks_overwatch.config.base_credentials import BaseCredentials
from stonks_overwatch.utils.core.localization import LocalizationUtility


@dataclass
class IbkrCredentials(BaseCredentials):
    access_token: str
    access_token_secret: str
    consumer_key: str
    dh_prime: str
    encryption_key_fp: str
    signature_key_fp: str

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "IbkrCredentials":
        if not data:
            return cls("", "")
        return cls(**data)


class IbkrConfig(BaseConfig):
    config_key = "ibkr"
    # As per https://www.interactivebrokers.com/campus/ibkr-api-page/cpapi-v1/#pacing-limitations
    # Some endpoints have a limit of 15 requests per minute: ie: /pa/transactions
    DEFAULT_IBKR_UPDATE_FREQUENCY = 15
    DEFAULT_IBKR_START_DATE_STR = "2020-01-01"
    DEFAULT_IBKR_START_DATE = LocalizationUtility.convert_string_to_date(DEFAULT_IBKR_START_DATE_STR)

    def __init__(
        self,
        credentials: Optional[IbkrCredentials],
        start_date: date,
        update_frequency_minutes: int = DEFAULT_IBKR_UPDATE_FREQUENCY,
        enabled: bool = True,
    ) -> None:
        super().__init__(credentials, enabled)
        if update_frequency_minutes < 1:
            raise ValueError("Update frequency must be at least 1 minute")
        self.start_date = start_date
        self.update_frequency_minutes = update_frequency_minutes

    def __eq__(self, value: object) -> bool:
        if isinstance(value, IbkrConfig):
            return (
                super().__eq__(value)
                and self.start_date == value.start_date
                and self.update_frequency_minutes == value.update_frequency_minutes
            )
        return False

    def __repr__(self) -> str:
        return (
            f"IbkrConfig(enabled={self.enabled}, "
            f"credentials={self.credentials}, "
            f"start_date={self.start_date}, "
            f"update_frequency_minutes={self.update_frequency_minutes})"
        )

    @property
    def get_credentials(self) -> IbkrCredentials:
        return self.credentials

    @classmethod
    def from_dict(cls, data: dict) -> "IbkrConfig":
        enabled = data.get("enabled", True)
        credentials_data = data.get("credentials")
        credentials = IbkrCredentials.from_dict(credentials_data) if credentials_data else None
        start_date = data.get("start_date", cls.DEFAULT_IBKR_START_DATE)
        if isinstance(start_date, str):
            start_date = LocalizationUtility.convert_string_to_date(start_date)
        update_frequency_minutes = data.get("update_frequency_minutes", cls.DEFAULT_IBKR_UPDATE_FREQUENCY)

        return cls(credentials, start_date, update_frequency_minutes, enabled)

    @classmethod
    def default(cls) -> "IbkrConfig":
        try:
            return cls.from_json_file(cls.CONFIG_PATH)
        except Exception:
            cls.logger.debug("Cannot find IBKR configuration file. Using default values")
            return IbkrConfig(
                credentials=None,
                start_date=cls.DEFAULT_IBKR_START_DATE,
                update_frequency_minutes=cls.DEFAULT_IBKR_UPDATE_FREQUENCY,
            )
