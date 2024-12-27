import json
import logging
from dataclasses import dataclass
from datetime import date, datetime
from pathlib import Path
from typing import Any, Dict, Optional

from settings import PROJECT_PATH


@dataclass
class DegiroCredentials:
    username: str
    password: str
    int_account: Optional[int] = None
    totp_secret_key: Optional[str] = None
    one_time_password: Optional[int] = None

    def to_dict(self) -> dict:
        return {
            "username": self.username,
            "password": self.password,
            "int_account": self.int_account,
            "totp_secret_key": self.totp_secret_key,
            "one_time_password": self.one_time_password,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "DegiroCredentials":
        if not data:
            return cls("", "")
        return cls(
            username=data.get("username", ""),
            password=data.get("password", ""),
            int_account=data.get("int_account"),
            totp_secret_key=data.get("totp_secret_key"),
            one_time_password=data.get("one_time_password"),
        )

    @classmethod
    def from_request(cls, request) -> "DegiroCredentials":
        session_credentials = request.session.get("credentials", {})
        return cls(
            username=session_credentials.get("username", ""),
            password=session_credentials.get("password", ""),
            int_account=session_credentials.get("int_account"),
            totp_secret_key=session_credentials.get("totp_secret_key"),
            one_time_password=session_credentials.get("one_time_password"),
        )

degiro_config_logger = logging.getLogger("stocks_portfolio.degiro_config")

class DegiroConfig:
    DEGIRO_CONFIG_PATH = Path(PROJECT_PATH) / "config" / "config.json"
    DEFAULT_BASE_CURRENCY = "EUR"
    DEFAULT_DEGIRO_UPDATE_FREQUENCY = 5
    DEFAULT_DEGIRO_START_DATE = "2020-01-01"

    def __init__(
            self,
            credentials: Optional[DegiroCredentials],
            base_currency: Optional[str],
            start_date: date,
            update_frequency_minutes: int = DEFAULT_DEGIRO_UPDATE_FREQUENCY
    ) -> None:
        if update_frequency_minutes < 1:
            raise ValueError("Update frequency must be at least 1 minute")
        if base_currency and not isinstance(base_currency, str):
            raise TypeError("base_currency must be a string")
        self.credentials = credentials
        self.base_currency = base_currency
        self.start_date = start_date
        self.update_frequency_minutes = update_frequency_minutes

    def __eq__(self, value: object) -> bool:
        if isinstance(value, DegiroConfig):
            return (
                self.credentials == value.credentials
                and self.base_currency == value.base_currency
                and self.start_date == value.start_date
            )
        return False

    def __repr__(self) -> str:
        return (f"DegiroConfig(credentials={self.credentials}, "
                f"base_currency={self.base_currency}, "
                f"start_date={self.start_date}, "
                f"update_frequency_minutes={self.update_frequency_minutes})")

    @classmethod
    def from_dict(cls, data: dict) -> "DegiroConfig":
        credentials_data = data.get("credentials")
        credentials = DegiroCredentials.from_dict(credentials_data) if credentials_data else None
        base_currency = data.get("base_currency", "")
        start_date_str = data.get("start_date", cls.DEFAULT_DEGIRO_START_DATE)
        # FIXME: Use Localization method
        start_date = datetime.strptime(start_date_str, "%Y-%m-%d").date() if start_date_str else date.today()
        update_frequency_minutes = data.get("update_frequency_minutes", cls.DEFAULT_DEGIRO_UPDATE_FREQUENCY)

        return cls(credentials, base_currency, start_date, update_frequency_minutes)

    @classmethod
    def from_json_file(cls, file_path: str | Path) -> "DegiroConfig":
        """Loads the configuration from a JSON file."""
        data = {}
        with open(file_path, "r") as f:
            data = json.load(f)
        return cls.from_dict(data.get("degiro", {}))

    @classmethod
    def default(cls) -> "DegiroConfig":
        try:
            return cls.from_json_file(cls.DEGIRO_CONFIG_PATH)
        except Exception:
            degiro_config_logger.warning("Cannot find configuration file. Using default values")
            return DegiroConfig(
                credentials=None,
                base_currency=cls.DEFAULT_BASE_CURRENCY,
                start_date=date.today(),
                update_frequency_minutes=cls.DEFAULT_DEGIRO_UPDATE_FREQUENCY
            )
