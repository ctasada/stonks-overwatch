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

    def __init__(
        self,
        credentials: Optional[BitvavoCredentials],
        enabled: bool = True,
    ) -> None:
        super().__init__(credentials, enabled)

    @property
    def get_credentials(self) -> BitvavoCredentials:
        return self.credentials

    @classmethod
    def from_dict(cls, data: dict) -> "BitvavoConfig":
        enabled = data.get("enabled", True)
        credentials_data = data.get("credentials")
        credentials = BitvavoCredentials.from_dict(credentials_data) if credentials_data else None

        return cls(credentials, enabled)

    @classmethod
    def default(cls) -> "BitvavoConfig":
        try:
            return cls.from_json_file(cls.CONFIG_PATH)
        except Exception:
            cls.logger.debug("Cannot find BITVAVO configuration file. Using default values")
            return BitvavoConfig(
                credentials=None,
            )
