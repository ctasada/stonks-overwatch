import json
from pathlib import Path
from typing import Optional

from stonks_overwatch.config.bitvavo_config import BitvavoConfig
from stonks_overwatch.config.degiro_config import DegiroConfig
from stonks_overwatch.services.degiro.degiro_service import DeGiroService
from stonks_overwatch.services.models import PortfolioId
from stonks_overwatch.utils.logger import StonksLogger


class Config:

    logger = StonksLogger.get_logger("stocks_portfolio.config", "[CONFIG]")

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

    def is_enabled(self, selected_portfolio: PortfolioId) -> bool:
        if selected_portfolio == PortfolioId.DEGIRO:
            return self.is_degiro_enabled(selected_portfolio)
        if selected_portfolio == PortfolioId.BITVAVO:
            return self.is_bitvavo_enabled(selected_portfolio)

        return False

    def is_degiro_enabled(self, selected_portfolio: PortfolioId = PortfolioId.ALL) -> bool:
        return (self.degiro_configuration.is_enabled()
                and (DeGiroService().check_connection()
                    or (self.degiro_configuration is not None
                    and self.degiro_configuration.credentials is not None)
                )
                and selected_portfolio in [PortfolioId.ALL, PortfolioId.DEGIRO])

    def is_bitvavo_enabled(self, selected_portfolio: PortfolioId = PortfolioId.ALL) -> bool:
        return (self.bitvavo_configuration.is_enabled()
                and self.bitvavo_configuration is not None
                and self.bitvavo_configuration.credentials is not None
                and selected_portfolio in [PortfolioId.ALL, PortfolioId.BITVAVO])

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
        return Config(
            base_currency=Config.DEFAULT_BASE_CURRENCY,
            degiro_configuration=DegiroConfig.default(),
            bitvavo_configuration=BitvavoConfig.default(),
        )
