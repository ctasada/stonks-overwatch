import json
import os
from abc import abstractmethod
from pathlib import Path
from typing import Optional

from settings import PROJECT_PATH
from stonks_overwatch.config.base_credentials import BaseCredentials
from stonks_overwatch.utils.logger import StonksLogger

class BaseConfig:
    logger = StonksLogger.get_logger("stocks_portfolio.config", "[BASE_CONFIG]")
    CONFIG_PATH = os.path.join(PROJECT_PATH, "config", "config.json")

    def __init__(
            self,
            credentials: Optional[BaseCredentials],
            enabled: bool = True,
    ) -> None:
        self.enabled = enabled
        self.credentials = credentials

    def __eq__(self, value: object) -> bool:
        if isinstance(value, self.__class__):
            return self.credentials == value.credentials
        return False

    def __repr__(self) -> str:
        return f"{self.__class__.__name__}(enabled={self.enabled}, credentials={self.credentials})"

    def is_enabled(self) -> bool:
        return self.enabled

    @property
    @abstractmethod
    def get_credentials(self):
        pass

    @classmethod
    def from_json_file(cls, file_path: str | Path) -> "BaseConfig":
        """Loads the configuration from a JSON file."""
        data = {}
        with open(file_path, "r") as f:
            data = json.load(f)
        return cls.from_dict(data.get(cls.config_key, {}))
