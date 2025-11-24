import os
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
            return cls("", "", "", "", "", "")
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
        enabled: bool = False,
        offline_mode: bool = None,
    ) -> None:
        if offline_mode is None:
            offline_mode = os.getenv("DEMO_MODE", False) in [True, "true", "True", "1"]

        self.logger.info(f"Initializing IbkrConfig with offline_mode={offline_mode}")
        super().__init__(credentials, start_date, enabled, offline_mode, update_frequency_minutes)

    def __eq__(self, value: object) -> bool:
        if isinstance(value, IbkrConfig):
            return super().__eq__(value)
        return False

    def __repr__(self) -> str:
        return (
            f"IbkrConfig(enabled={self.enabled}, "
            f"offline_mode={self.offline_mode}, "
            f"credentials={self.credentials}, "
            f"start_date={self.start_date}, "
            f"update_frequency_minutes={self.update_frequency_minutes})"
        )

    @property
    def get_credentials(self) -> IbkrCredentials:
        return self.credentials

    @classmethod
    def from_dict(cls, data: dict) -> "IbkrConfig":
        enabled = data.get("enabled", False)
        credentials_data = data.get("credentials")
        credentials = IbkrCredentials.from_dict(credentials_data) if credentials_data else None
        start_date = data.get("start_date", cls.DEFAULT_IBKR_START_DATE)
        if isinstance(start_date, str):
            start_date = LocalizationUtility.convert_string_to_date(start_date)
        update_frequency_minutes = data.get("update_frequency_minutes", cls.DEFAULT_IBKR_UPDATE_FREQUENCY)

        demo_mode = os.getenv("DEMO_MODE", False) in [True, "true", "True", "1"]
        if demo_mode:
            offline_mode = True
        else:
            # Only use offline_mode from data if explicitly set, otherwise let constructor check DEMO_MODE
            offline_mode = data.get("offline_mode") if "offline_mode" in data else None

        return cls(credentials, start_date, update_frequency_minutes, enabled, offline_mode)

    @classmethod
    def default(cls) -> "IbkrConfig":
        try:
            return cls.from_db_with_json_override("ibkr")
        except Exception:
            cls.logger.debug("Cannot find IBKR configuration file. Using default values")
            return IbkrConfig(
                credentials=None,
                start_date=cls.DEFAULT_IBKR_START_DATE,
                update_frequency_minutes=cls.DEFAULT_IBKR_UPDATE_FREQUENCY,
            )
