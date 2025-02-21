import json
import logging
from pathlib import Path
from typing import Optional

from settings import PROJECT_PATH
from stonks_overwatch.config.base_credentials import BaseCredentials


class BaseConfig:
    logger = logging.getLogger("stocks_portfolio.config")
    CONFIG_PATH = Path(PROJECT_PATH) / "config" / "config.json"

    def __init__(self, credentials: Optional[BaseCredentials]) -> None:
        self.credentials = credentials

    def __eq__(self, value: object) -> bool:
        if isinstance(value, self.__class__):
            return self.credentials == value.credentials
        return False

    def __repr__(self) -> str:
        return f"{self.__class__.__name__}(credentials={self.credentials})"

    @classmethod
    def from_json_file(cls, file_path: str | Path) -> "BaseConfig":
        """Loads the configuration from a JSON file."""
        data = {}
        with open(file_path, "r") as f:
            data = json.load(f)
        return cls.from_dict(data.get(cls.config_key, {}))
