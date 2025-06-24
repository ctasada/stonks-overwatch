from datetime import date
from typing import Optional

from stonks_overwatch.config.base_config import BaseConfig
from stonks_overwatch.config.degiro_credentials import DegiroCredentials
from stonks_overwatch.utils.core.localization import LocalizationUtility


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
        super().__init__(credentials, enabled)
        if update_frequency_minutes < 1:
            raise ValueError("Update frequency must be at least 1 minute")
        self.start_date = start_date
        self.update_frequency_minutes = update_frequency_minutes
        self.offline_mode = offline_mode

    def __eq__(self, value: object) -> bool:
        if isinstance(value, DegiroConfig):
            return (
                super().__eq__(value)
                and self.start_date == value.start_date
                and self.update_frequency_minutes == value.update_frequency_minutes
                and self.offline_mode == value.offline_mode
            )
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
            return cls.from_json_file(cls.CONFIG_PATH)
        except Exception:
            cls.logger.debug("Cannot find DEGIRO configuration file. Using default values")
            return DegiroConfig(
                credentials=None,
                start_date=cls.DEFAULT_DEGIRO_START_DATE,
                update_frequency_minutes=cls.DEFAULT_DEGIRO_UPDATE_FREQUENCY,
            )
