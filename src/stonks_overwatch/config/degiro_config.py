from datetime import date, datetime
from typing import Optional

from stonks_overwatch.config.base_config import BaseConfig
from stonks_overwatch.config.degiro_credentials import DegiroCredentials


class DegiroConfig(BaseConfig):
    config_key = "degiro"
    DEFAULT_DEGIRO_UPDATE_FREQUENCY = 5
    DEFAULT_DEGIRO_START_DATE = "2020-01-01"

    def __init__(
            self,
            credentials: Optional[DegiroCredentials],
            start_date: date,
            update_frequency_minutes: int = DEFAULT_DEGIRO_UPDATE_FREQUENCY
    ) -> None:
        super().__init__(credentials)
        if update_frequency_minutes < 1:
            raise ValueError("Update frequency must be at least 1 minute")
        self.start_date = start_date
        self.update_frequency_minutes = update_frequency_minutes

    def __eq__(self, value: object) -> bool:
        if isinstance(value, DegiroConfig):
            return (
                    super().__eq__(value) and
                    self.start_date == value.start_date and
                    self.update_frequency_minutes == value.update_frequency_minutes
            )
        return False

    def __repr__(self) -> str:
        return (f"DegiroConfig(credentials={self.credentials}, "
                f"start_date={self.start_date}, "
                f"update_frequency_minutes={self.update_frequency_minutes})")

    @classmethod
    def from_dict(cls, data: dict) -> "DegiroConfig":
        credentials_data = data.get("credentials")
        credentials = DegiroCredentials.from_dict(credentials_data) if credentials_data else None
        start_date_str = data.get("start_date", cls.DEFAULT_DEGIRO_START_DATE)
        # FIXME: Use Localization method
        start_date = datetime.strptime(start_date_str, "%Y-%m-%d").date() if start_date_str else date.today()
        update_frequency_minutes = data.get("update_frequency_minutes", cls.DEFAULT_DEGIRO_UPDATE_FREQUENCY)

        return cls(credentials, start_date, update_frequency_minutes)

    @classmethod
    def default(cls) -> "DegiroConfig":
        try:
            return cls.from_json_file(cls.CONFIG_PATH)
        except Exception:
            cls.logger.warning("Cannot find DeGiro configuration file. Using default values")
            return DegiroConfig(
                credentials=None,
                start_date=date.today(),
                update_frequency_minutes=cls.DEFAULT_DEGIRO_UPDATE_FREQUENCY
            )
