import os
from dataclasses import dataclass
from datetime import date
from typing import Any, Dict, Optional

from stonks_overwatch.config.base_config import BaseConfig
from stonks_overwatch.config.base_credentials import BaseCredentials
from stonks_overwatch.constants import BrokerName
from stonks_overwatch.utils.core.localization import LocalizationUtility


@dataclass
class Metatrader4Credentials(BaseCredentials):
    ftp_server: str
    username: str
    password: str
    path: str

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Metatrader4Credentials":
        if not data:
            return cls("", "", "", "")
        return cls(**data)

    def has_minimal_credentials(self) -> bool:
        return bool(self.ftp_server and self.username and self.password and self.path)

    def to_auth_params(self) -> dict:
        """
        Convert credentials to authentication parameters.

        Returns:
            Dictionary with authentication parameters for MetaTrader4 auth service

        Note:
            remember_me is intentionally omitted as this method is used for
            auto-authentication with already-stored credentials. The auth service
            will use its default value (False).
        """
        return {
            "ftp_server": self.ftp_server,
            "username": self.username,
            "password": self.password,
            "path": self.path,
        }


class Metatrader4Config(BaseConfig):
    config_key = BrokerName.METATRADER4
    DEFAULT_MT4_UPDATE_FREQUENCY = 60
    DEFAULT_MT4_START_DATE_STR = "2020-01-01"
    DEFAULT_MT4_START_DATE = LocalizationUtility.convert_string_to_date(DEFAULT_MT4_START_DATE_STR)

    def __init__(
        self,
        credentials: Optional[Metatrader4Credentials],
        start_date: date,
        update_frequency_minutes: int = DEFAULT_MT4_UPDATE_FREQUENCY,
        enabled: bool = True,
        offline_mode: bool = None,
    ) -> None:
        if offline_mode is None:
            offline_mode = os.getenv("DEMO_MODE", False) in [True, "true", "True", "1"]

        self.logger.info(f"Initializing Metatrader4Config with offline_mode={offline_mode}")
        super().__init__(credentials, start_date, enabled, offline_mode, update_frequency_minutes)

    def __eq__(self, value: object) -> bool:
        if isinstance(value, Metatrader4Config):
            return super().__eq__(value)
        return False

    def __repr__(self) -> str:
        return (
            f"Metatrader4Config(enabled={self.enabled}, "
            f"offline_mode={self.offline_mode}, "
            f"credentials={self.credentials}, "
            f"start_date={self.start_date}, "
            f"update_frequency_minutes={self.update_frequency_minutes})"
        )

    @property
    def get_credentials(self) -> Metatrader4Credentials:
        return self.credentials

    @classmethod
    def from_dict(cls, data: dict) -> "Metatrader4Config":
        enabled = data.get("enabled", True)
        credentials_data = data.get("credentials")
        credentials = Metatrader4Credentials.from_dict(credentials_data) if credentials_data else None
        start_date = data.get("start_date", cls.DEFAULT_MT4_START_DATE)
        if isinstance(start_date, str):
            start_date = LocalizationUtility.convert_string_to_date(start_date)
        update_frequency_minutes = data.get("update_frequency_minutes", cls.DEFAULT_MT4_UPDATE_FREQUENCY)

        demo_mode = os.getenv("DEMO_MODE", False) in [True, "true", "True", "1"]
        if demo_mode:
            offline_mode = True
        else:
            # Only use offline_mode from data if explicitly set, otherwise let constructor check DEMO_MODE
            offline_mode = data.get("offline_mode") if "offline_mode" in data else None

        return cls(credentials, start_date, update_frequency_minutes, enabled, offline_mode)

    @classmethod
    def default(cls) -> "Metatrader4Config":
        try:
            return cls.from_db_with_json_override(BrokerName.METATRADER4)
        except Exception:
            cls.logger.debug("Cannot find Metatrader4 configuration file. Using default values")
            return Metatrader4Config(
                credentials=None,
                start_date=cls.DEFAULT_MT4_START_DATE,
                update_frequency_minutes=cls.DEFAULT_MT4_UPDATE_FREQUENCY,
            )
