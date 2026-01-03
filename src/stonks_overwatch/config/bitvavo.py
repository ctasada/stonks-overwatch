import os
from dataclasses import dataclass
from datetime import date
from typing import Any, Dict, Optional

from stonks_overwatch.config.base_config import BaseConfig
from stonks_overwatch.config.base_credentials import BaseCredentials
from stonks_overwatch.utils.core.localization import LocalizationUtility


@dataclass
class BitvavoCredentials(BaseCredentials):
    apikey: str
    apisecret: str

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "BitvavoCredentials":
        if not data:
            return cls("", "")
        return cls(**data)

    @classmethod
    def from_request(cls, request) -> "BitvavoCredentials":
        """Create credentials from Django request session."""
        session_credentials = request.session.get("bitvavo_credentials", {})
        return cls.from_dict(session_credentials)

    def has_minimal_credentials(self) -> bool:
        """Check if minimal credentials are provided."""
        return bool(self.apikey and self.apisecret)


class BitvavoConfig(BaseConfig):
    config_key = "bitvavo"
    DEFAULT_BITVAVO_UPDATE_FREQUENCY = 5
    DEFAULT_BITVAVO_START_DATE_STR = "2020-01-01"
    DEFAULT_BITVAVO_START_DATE = LocalizationUtility.convert_string_to_date(DEFAULT_BITVAVO_START_DATE_STR)

    def __init__(
        self,
        credentials: Optional[BitvavoCredentials],
        start_date: date,
        update_frequency_minutes: int = DEFAULT_BITVAVO_UPDATE_FREQUENCY,
        enabled: bool = False,
        offline_mode: bool = None,
    ) -> None:
        if offline_mode is None:
            offline_mode = os.getenv("DEMO_MODE", False) in [True, "true", "True", "1"]

        self.logger.info(f"Initializing BitvavoConfig with offline_mode={offline_mode}")
        super().__init__(credentials, start_date, enabled, offline_mode, update_frequency_minutes)

    def __eq__(self, value: object) -> bool:
        if isinstance(value, BitvavoConfig):
            return super().__eq__(value)
        return False

    def __repr__(self) -> str:
        return (
            f"BitvavoConfig(enabled={self.enabled}, "
            f"offline_mode={self.offline_mode}, "
            f"credentials={self.credentials}, "
            f"start_date={self.start_date}, "
            f"update_frequency_minutes={self.update_frequency_minutes})"
        )

    @property
    def get_credentials(self) -> BitvavoCredentials:
        return self.credentials

    @classmethod
    def from_dict(cls, data: dict) -> "BitvavoConfig":
        enabled = data.get("enabled", False)
        credentials_data = data.get("credentials")
        credentials = BitvavoCredentials.from_dict(credentials_data) if credentials_data else None
        start_date = data.get("start_date", cls.DEFAULT_BITVAVO_START_DATE)
        if isinstance(start_date, str):
            start_date = LocalizationUtility.convert_string_to_date(start_date)
        update_frequency_minutes = data.get("update_frequency_minutes", cls.DEFAULT_BITVAVO_UPDATE_FREQUENCY)

        demo_mode = os.getenv("DEMO_MODE", False) in [True, "true", "True", "1"]
        if demo_mode:
            offline_mode = True
        else:
            # Only use offline_mode from data if explicitly set, otherwise let constructor check DEMO_MODE
            offline_mode = data.get("offline_mode") if "offline_mode" in data else None

        return cls(credentials, start_date, update_frequency_minutes, enabled, offline_mode)

    @classmethod
    def default(cls) -> "BitvavoConfig":
        try:
            return cls.from_db_with_json_override("bitvavo")
        except Exception:
            cls.logger.debug("Cannot find BITVAVO configuration file. Using default values")
            return BitvavoConfig(
                credentials=None,
                start_date=cls.DEFAULT_BITVAVO_START_DATE,
                update_frequency_minutes=cls.DEFAULT_BITVAVO_UPDATE_FREQUENCY,
            )
