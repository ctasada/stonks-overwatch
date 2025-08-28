from dataclasses import dataclass
from datetime import date
from typing import Any, Dict, Optional

from stonks_overwatch.config.base_config import BaseConfig
from stonks_overwatch.config.base_credentials import BaseCredentials
from stonks_overwatch.utils.core.localization import LocalizationUtility


@dataclass
class DegiroCredentials(BaseCredentials):
    username: str
    password: str
    int_account: Optional[int] = None
    totp_secret_key: Optional[str] = None
    one_time_password: Optional[int] = None
    remember_me: Optional[bool] = None

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "DegiroCredentials":
        if not data:
            return cls("", "")
        return cls(**data)

    @classmethod
    def from_request(cls, request) -> "DegiroCredentials":
        session_credentials = request.session.get("credentials", {})
        return cls.from_dict(session_credentials)

    def has_minimal_credentials(self) -> bool:
        return bool(self.username and self.password and (self.totp_secret_key or self.one_time_password))


class DegiroConfig(BaseConfig):
    config_key = "degiro"
    DEFAULT_DEGIRO_UPDATE_FREQUENCY = 5
    DEFAULT_DEGIRO_START_DATE_STR = "2020-01-01"
    DEFAULT_DEGIRO_START_DATE = LocalizationUtility.convert_string_to_date(DEFAULT_DEGIRO_START_DATE_STR)

    def __init__(
        self,
        credentials: Optional[DegiroCredentials],
        start_date: date,
        update_frequency_minutes: int = DEFAULT_DEGIRO_UPDATE_FREQUENCY,
        enabled: bool = True,
        offline_mode: bool = False,
    ) -> None:
        super().__init__(credentials, start_date, enabled, offline_mode, update_frequency_minutes)

    def __eq__(self, value: object) -> bool:
        if isinstance(value, DegiroConfig):
            return super().__eq__(value)
        return False

    def __repr__(self) -> str:
        return (
            f"DegiroConfig(enabled={self.enabled}, "
            f"offline_mode={self.offline_mode}, "
            f"credentials={self.credentials}, "
            f"start_date={self.start_date}, "
            f"update_frequency_minutes={self.update_frequency_minutes})"
        )

    @property
    def get_credentials(self) -> DegiroCredentials:
        return self.credentials

    @classmethod
    def from_dict(cls, data: dict) -> "DegiroConfig":
        enabled = data.get("enabled", True)
        credentials_data = data.get("credentials")
        credentials = DegiroCredentials.from_dict(credentials_data) if credentials_data else None
        start_date = data.get("start_date", cls.DEFAULT_DEGIRO_START_DATE)
        if isinstance(start_date, str):
            start_date = LocalizationUtility.convert_string_to_date(start_date)
        update_frequency_minutes = data.get("update_frequency_minutes", cls.DEFAULT_DEGIRO_UPDATE_FREQUENCY)
        offline_mode = data.get("offline_mode", False)

        return cls(credentials, start_date, update_frequency_minutes, enabled, offline_mode)

    @classmethod
    def default(cls) -> "DegiroConfig":
        try:
            return cls.from_db_with_json_override("degiro")
        except Exception:
            cls.logger.debug("Cannot find DEGIRO configuration file. Using default values")
            return DegiroConfig(
                credentials=None,
                start_date=cls.DEFAULT_DEGIRO_START_DATE,
                update_frequency_minutes=cls.DEFAULT_DEGIRO_UPDATE_FREQUENCY,
            )
