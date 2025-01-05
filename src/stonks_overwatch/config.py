import json
import logging
from dataclasses import dataclass
from datetime import date, datetime
from pathlib import Path
from typing import Any, Dict, Optional

from settings import PROJECT_PATH

config_logger = logging.getLogger("stocks_portfolio.config")

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

class DegiroConfig:
    DEFAULT_DEGIRO_UPDATE_FREQUENCY = 5
    DEFAULT_DEGIRO_START_DATE = "2020-01-01"

    def __init__(
            self,
            credentials: Optional[DegiroCredentials],
            start_date: date,
            update_frequency_minutes: int = DEFAULT_DEGIRO_UPDATE_FREQUENCY
    ) -> None:
        if update_frequency_minutes < 1:
            raise ValueError("Update frequency must be at least 1 minute")
        self.credentials = credentials
        self.start_date = start_date
        self.update_frequency_minutes = update_frequency_minutes

    def __eq__(self, value: object) -> bool:
        if isinstance(value, DegiroConfig):
            return (
                self.credentials == value.credentials
                and self.start_date == value.start_date
                and self.update_frequency_minutes == value.update_frequency_minutes
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
    def from_json_file(cls, file_path: str | Path) -> "DegiroConfig":
        """Loads the configuration from a JSON file."""
        data = {}
        with open(file_path, "r") as f:
            data = json.load(f)
        return cls.from_dict(data.get("degiro", {}))

    @classmethod
    def default(cls) -> "DegiroConfig":
        try:
            return cls.from_json_file(Config.CONFIG_PATH)
        except Exception:
            config_logger.warning("Cannot find configuration file. Using default values")
            return DegiroConfig(
                credentials=None,
                start_date=date.today(),
                update_frequency_minutes=cls.DEFAULT_DEGIRO_UPDATE_FREQUENCY
            )


@dataclass
class BitvavoCredentials:
    apikey: str
    apisecret: str

    def to_dict(self) -> dict:
        return {
            "apiKey": self.apikey,
            "apiSecret": self.apisecret,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "BitvavoCredentials":
        if not data:
            return cls("", "")
        return cls(
            apikey=data.get("apiKey", ""),
            apisecret=data.get("apiSecret", ""),
        )

class BitvavoConfig:
    BITVAVO_CONFIG_PATH = Path(PROJECT_PATH) / "config" / "config.json"

    def __init__(
            self,
            credentials: Optional[BitvavoCredentials],
    ) -> None:
        self.credentials = credentials

    def __eq__(self, value: object) -> bool:
        if isinstance(value, BitvavoConfig):
            return (
                    self.credentials == value.credentials
            )
        return False

    def __repr__(self) -> str:
        return (f"BitvavoConfig(credentials={self.credentials}, "
                ")")

    @classmethod
    def from_dict(cls, data: dict) -> "BitvavoConfig":
        credentials_data = data.get("credentials")
        credentials = BitvavoCredentials.from_dict(credentials_data) if credentials_data else None

        return cls(credentials)

    @classmethod
    def from_json_file(cls, file_path: str | Path) -> "BitvavoConfig":
        """Loads the configuration from a JSON file."""
        data = {}
        with open(file_path, "r") as f:
            data = json.load(f)
        return cls.from_dict(data.get("bitvavo", {}))

    @classmethod
    def default(cls) -> "BitvavoConfig":
        try:
            return cls.from_json_file(cls.BITVAVO_CONFIG_PATH)
        except Exception:
            config_logger.warning("Cannot find configuration file. Using default values")
            return BitvavoConfig(
                credentials=None,
            )

class Config:
    CONFIG_PATH = Path(PROJECT_PATH) / "config" / "config.json"
    DEFAULT_BASE_CURRENCY: str = "EUR"

    base_currency = DEFAULT_BASE_CURRENCY
    degiro_configuration: Optional[DegiroConfig] = None
    bitvavo_configuration: Optional[BitvavoConfig] = None

    def __init__(
            self,
            base_currency: Optional[str] = DEFAULT_BASE_CURRENCY,
            degiro_configuration: Optional[DegiroConfig] = None,
            bitvavo_configuration: Optional[BitvavoConfig] = None,
    ) -> None:
        if base_currency and not isinstance(base_currency, str):
            raise TypeError("base_currency must be a string")
        self.base_currency = base_currency

        self.degiro_configuration = degiro_configuration
        self.bitvavo_configuration = bitvavo_configuration

    def is_degiro_enabled(self) -> bool:
        return self.degiro_configuration is not None and self.degiro_configuration.credentials is not None

    def is_bitvavo_enabled(self) -> bool:
        return self.bitvavo_configuration is not None and self.bitvavo_configuration.credentials is not None

    def __eq__(self, value: object) -> bool:
        if isinstance(value, Config):
            return (
                    self.base_currency == value.base_currency and
                    self.degiro_configuration == value.degiro_configuration and
                    self.bitvavo_configuration == value.bitvavo_configuration
            )
        return False

    def __repr__(self) -> str:
        return (f"Config(base_currency={self.base_currency}, "
                f"degiro={self.degiro_configuration}, "
                f"bitvavo={self.bitvavo_configuration}, "
                ")")

    @classmethod
    def from_dict(cls, data: dict) -> "Config":
        base_currency = data.get("base_currency", Config.DEFAULT_BASE_CURRENCY)
        degiro_configuration = DegiroConfig.from_dict(data.get("degiro", {}))
        bitvavo_configuration = BitvavoConfig.from_dict(data.get("bitvavo", {}))

        return cls(base_currency, degiro_configuration, bitvavo_configuration)

    @classmethod
    def from_json_file(cls, file_path: str | Path) -> "Config":
        """Loads the configuration from a JSON file."""
        data = {}
        with open(file_path, "r") as f:
            data = json.load(f)
        return cls.from_dict(data)

    @classmethod
    def default(cls) -> "Config":
        try:
            return cls.from_json_file(Config.CONFIG_PATH)
        except Exception:
            config_logger.warning("Cannot find configuration file. Using default values")
            return Config(
                base_currency=Config.DEFAULT_BASE_CURRENCY,
                degiro_configuration=DegiroConfig.default(),
                bitvavo_configuration=BitvavoConfig.default(),
            )
