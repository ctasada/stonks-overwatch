from dataclasses import dataclass
from typing import Optional

from stonks_overwatch.config.base_config import BaseConfig
from stonks_overwatch.config.base_credentials import BaseCredentials


@dataclass
class BitvavoCredentials(BaseCredentials):
    apikey: str
    apisecret: str

    @classmethod
    def from_dict(cls, data: dict) -> "BitvavoCredentials":
        if not data:
            return cls("", "")
        return cls(**data)


class BitvavoConfig(BaseConfig):
    config_key = "bitvavo"
    DEFAULT_BITVAVO_UPDATE_FREQUENCY = 5

    def __init__(
        self,
        credentials: Optional[BitvavoCredentials],
        update_frequency_minutes: int = DEFAULT_BITVAVO_UPDATE_FREQUENCY,
        enabled: bool = True,
        offline_mode: bool = False,
    ) -> None:
        super().__init__(credentials, enabled)
        if update_frequency_minutes < 1:
            raise ValueError("Update frequency must be at least 1 minute")
        self.update_frequency_minutes = update_frequency_minutes
        self.offline_mode = offline_mode

    def __eq__(self, value: object) -> bool:
        if isinstance(value, BitvavoConfig):
            return (
                super().__eq__(value)
                and self.update_frequency_minutes == value.update_frequency_minutes
                and self.offline_mode == value.offline_mode
            )
        return False

    def __repr__(self) -> str:
        return (
            f"BitvavoConfig(enabled={self.enabled}, "
            f"offline_mode={self.offline_mode}, "
            f"credentials={self.credentials}, "
            f"update_frequency_minutes={self.update_frequency_minutes})"
        )

    @property
    def get_credentials(self) -> BitvavoCredentials:
        return self.credentials

    @classmethod
    def from_dict(cls, data: dict) -> "BitvavoConfig":
        enabled = data.get("enabled", True)
        credentials_data = data.get("credentials")
        credentials = BitvavoCredentials.from_dict(credentials_data) if credentials_data else None
        update_frequency_minutes = data.get("update_frequency_minutes", cls.DEFAULT_BITVAVO_UPDATE_FREQUENCY)
        offline_mode = data.get("offline_mode", False)

        return cls(credentials, update_frequency_minutes, enabled, offline_mode)

    @classmethod
    def default(cls) -> "BitvavoConfig":
        try:
            return cls.from_json_file(cls.CONFIG_PATH)
        except Exception:
            cls.logger.debug("Cannot find BITVAVO configuration file. Using default values")
            return BitvavoConfig(
                credentials=None,
                update_frequency_minutes=cls.DEFAULT_BITVAVO_UPDATE_FREQUENCY,
            )
