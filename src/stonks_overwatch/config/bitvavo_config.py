from typing import Optional

from stonks_overwatch.config.base_config import BaseConfig
from stonks_overwatch.config.bitvavo_credentials import BitvavoCredentials


class BitvavoConfig(BaseConfig):
    config_key = "bitvavo"

    def __init__(
            self,
            credentials: Optional[BitvavoCredentials],
    ) -> None:
        super().__init__(credentials)

    @classmethod
    def from_dict(cls, data: dict) -> "BitvavoConfig":
        credentials_data = data.get("credentials")
        credentials = BitvavoCredentials.from_dict(credentials_data) if credentials_data else None

        return cls(credentials)

    @classmethod
    def default(cls) -> "BitvavoConfig":
        try:
            return cls.from_json_file(cls.CONFIG_PATH)
        except Exception:
            cls.logger.warning("Cannot find configuration file. Using default values")
            return BitvavoConfig(
                credentials=None,
            )
