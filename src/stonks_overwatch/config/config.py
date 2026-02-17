import json
from pathlib import Path
from typing import Optional

from stonks_overwatch.config.base_config import BaseConfig
from stonks_overwatch.constants import BrokerName
from stonks_overwatch.core.factories.broker_factory import BrokerFactory
from stonks_overwatch.core.models import GlobalConfiguration
from stonks_overwatch.core.service_types import ServiceType
from stonks_overwatch.services.models import PortfolioId
from stonks_overwatch.utils.core.logger import StonksLogger
from stonks_overwatch.utils.core.logger_constants import LOGGER_CONFIG, TAG_CONFIG


class Config:
    """
    Main configuration class that provides access to all broker configurations.

    This class serves as the central configuration manager for the application,
    using the unified BrokerFactory for all broker operations.
    """

    logger = StonksLogger.get_logger(LOGGER_CONFIG, TAG_CONFIG)

    DEFAULT_BASE_CURRENCY: str = "EUR"

    def __init__(self, base_currency: Optional[str] = DEFAULT_BASE_CURRENCY) -> None:
        """
        Initialize configuration with base currency.

        Args:
            base_currency: The base currency for calculations
        """
        if base_currency and not isinstance(base_currency, str):
            raise TypeError("base_currency must be a string")

        self._base_currency = base_currency
        self._factory = BrokerFactory()
        self._settings_cache = {}
        self._loaded_from_db = False

    @property
    def base_currency(self) -> str:
        """
        Get the base currency for calculations.
        Priority: 1. JSON override, 2. DB setting, 3. Default
        """
        # 1. Check if it was passed in __init__ (usually from JSON file loading)
        if self._base_currency and self._base_currency != self.DEFAULT_BASE_CURRENCY:
            return self._base_currency

        # 2. Check DB setting
        db_value = self.get_setting("base_currency")
        if db_value:
            return db_value

        return self.DEFAULT_BASE_CURRENCY

    @base_currency.setter
    def base_currency(self, value: str) -> None:
        if not isinstance(value, str):
            raise TypeError("base_currency must be a string")
        self.save_setting("base_currency", value)

    @property
    def appearance(self) -> str:
        """
        Get the appearance setting (light, dark, auto).
        Priority: 1. JSON override (later), 2. DB setting, 3. Default
        """
        return self.get_setting("appearance", "auto")

    @appearance.setter
    def appearance(self, value: str) -> None:
        if value not in ["light", "dark", "auto"]:
            raise ValueError("appearance must be one of: light, dark, auto")
        self.save_setting("appearance", value)

    def get_setting(self, key: str, default: any = None) -> any:
        """
        Get an application-level setting.
        """
        if key not in self._settings_cache:
            try:
                # Use GlobalConfiguration model to fetch from DB
                self._settings_cache[key] = GlobalConfiguration.get_setting(key, default)
            except Exception as e:
                self.logger.warning(f"Failed to fetch setting '{key}' from database: {e}")
                return default
        return self._settings_cache.get(key, default)

    def save_setting(self, key: str, value: any) -> None:
        """
        Save an application-level setting.
        """
        try:
            GlobalConfiguration.set_setting(key, value)
            self._settings_cache[key] = value
            self.logger.info(f"Saved setting '{key}' with value '{value}'")
        except Exception as e:
            self.logger.error(f"Failed to save setting '{key}': {e}")
            raise

    def get_broker_config(self, broker_name: BrokerName) -> Optional[BaseConfig]:
        """
        Get a broker configuration using unified BrokerFactory.

        Args:
            broker_name: Name of the broker

        Returns:
            Configuration instance if available, None otherwise
        """
        return self._factory.create_config(broker_name)

    def is_enabled(self, selected_portfolio: PortfolioId) -> bool:
        """
        Check if any broker is enabled for the selected portfolio.

        Args:
            selected_portfolio: Selected portfolio filter

        Returns:
            True if any broker is enabled, False otherwise
        """
        if selected_portfolio == PortfolioId.ALL:
            # Check if any broker is enabled
            return any(self._is_broker_enabled(broker_name) for broker_name in self._factory.get_available_brokers())

        # For specific portfolio, check the corresponding broker
        try:
            broker_name = selected_portfolio.id if hasattr(selected_portfolio, "id") else str(selected_portfolio)
            return self._is_broker_enabled(broker_name)
        except (AttributeError, TypeError):
            return False

    def _is_broker_enabled(self, broker_name: BrokerName) -> bool:
        """
        Check if a specific broker is enabled.

        Args:
            broker_name: Name of the broker

        Returns:
            True if broker is enabled, False otherwise
        """
        config = self.get_broker_config(broker_name)
        return config.is_enabled() if config else False

    def get_capabilities(self, portfolio_id: PortfolioId) -> list[ServiceType]:
        """
        Get the capabilities (service types) for a portfolio.

        Args:
            portfolio_id: The portfolio to get capabilities for

        Returns:
            List of supported ServiceType enums
        """
        if portfolio_id == PortfolioId.ALL:
            capabilities = set()
            for broker_name in self._factory.get_available_brokers():
                if self._is_broker_enabled(broker_name):
                    capabilities.update(self._factory.get_broker_capabilities(broker_name))
            return sorted(capabilities, key=lambda x: x.value)

        if portfolio_id.broker_name:
            return self._factory.get_broker_capabilities(portfolio_id.broker_name)

        return []

    def __eq__(self, value: object) -> bool:
        if isinstance(value, Config):
            if self.base_currency != value.base_currency:
                return False
            self_brokers = set(self._factory.get_available_brokers())
            other_brokers = set(value._factory.get_available_brokers())
            if self_brokers != other_brokers:
                return False
            for broker in self_brokers:
                if self.get_broker_config(broker) != value.get_broker_config(broker):
                    return False
            return True
        return False

    def __repr__(self) -> str:
        # Get available brokers dynamically
        available_brokers = self._factory.get_available_brokers()
        broker_configs = {broker: self.get_broker_config(broker) for broker in available_brokers}

        broker_repr = ", ".join(f"{broker}_config={config}" for broker, config in broker_configs.items())

        return f"Config(base_currency={self.base_currency}, {broker_repr})"

    @classmethod
    def from_dict(cls, data: dict) -> "Config":
        """
        Create configuration from dictionary data.

        Args:
            data: Dictionary containing configuration data

        Returns:
            Config instance created from the data
        """
        base_currency = data.get("base_currency", cls.DEFAULT_BASE_CURRENCY)

        # Create config instance
        config = cls(base_currency)

        # Broker configurations are handled by BrokerFactory automatically
        # No need to manually create and set them - they're loaded on-demand

        return config

    @classmethod
    def from_json_file(cls, file_path: str | Path) -> "Config":
        """
        Create configuration from JSON file.

        Args:
            file_path: Path to the JSON configuration file

        Returns:
            Config instance loaded from the file
        """
        with open(file_path, "r") as f:
            data = json.load(f)

        return cls.from_dict(data)

    @classmethod
    def _default(cls) -> "Config":
        """
        Create default configuration.

        Returns:
            Config instance with default settings
        """
        return cls()

    @classmethod
    def get_global(cls) -> "Config":
        """
        Get the global configuration instance using cached access.

        This method provides cached access to the configuration,
        reducing redundant configuration creation and logging.

        Returns:
            The global configuration instance
        """
        # Use the singleton pattern with lazy initialization
        if not hasattr(cls, "_global_instance"):
            cls._global_instance = cls._default()
        return cls._global_instance

    @classmethod
    def reset_global_for_tests(cls) -> None:
        """
        Reset the global configuration instance for tests.

        This clears the cached global instance to force recreation
        from test configuration.
        """
        if hasattr(cls, "_global_instance"):
            delattr(cls, "_global_instance")

        # Also clear BrokerFactory cache
        from stonks_overwatch.core.factories.broker_factory import BrokerFactory

        factory = BrokerFactory()
        factory.clear_cache()
