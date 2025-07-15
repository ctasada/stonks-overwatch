import json
from pathlib import Path
from typing import Dict, Optional, Type

from stonks_overwatch.config.base_config import BaseConfig
from stonks_overwatch.config.bitvavo import BitvavoConfig
from stonks_overwatch.config.config_factory import config_factory
from stonks_overwatch.config.degiro import DegiroConfig
from stonks_overwatch.config.ibkr import IbkrConfig
from stonks_overwatch.services.models import PortfolioId
from stonks_overwatch.utils.core.logger import StonksLogger


class ConfigRegistry:
    """
    Registry for managing broker configurations dynamically.

    This class maintains a registry of broker configurations
    and provides a centralized way to manage them.
    """

    logger = StonksLogger.get_logger("stonks_overwatch.config", "[CONFIG_REGISTRY]")

    def __init__(self):
        self._broker_configs: Dict[str, BaseConfig] = {}
        self._broker_config_classes: Dict[str, Type[BaseConfig]] = {}

    def register_broker_config(self, broker_name: str, config_class: Type[BaseConfig]) -> None:
        """
        Register a broker configuration class.

        Args:
            broker_name: Name of the broker (e.g., 'degiro', 'bitvavo')
            config_class: Configuration class for the broker
        """
        self._broker_config_classes[broker_name] = config_class

    def set_broker_config(self, broker_name: str, config: BaseConfig) -> None:
        """
        Set a broker configuration instance.

        Args:
            broker_name: Name of the broker
            config: Configuration instance
        """
        self._broker_configs[broker_name] = config

    def get_broker_config(self, broker_name: str) -> Optional[BaseConfig]:
        """
        Get a broker configuration instance.

        Args:
            broker_name: Name of the broker

        Returns:
            Configuration instance if available, None otherwise
        """
        return self._broker_configs.get(broker_name)

    def get_available_brokers(self) -> list[str]:
        """
        Get the list of all registered brokers.

        Returns:
            List of broker names
        """
        return list(self._broker_configs.keys())

    def is_broker_enabled(self, broker_name: str, selected_portfolio: PortfolioId = PortfolioId.ALL) -> bool:
        """
        Check if a broker is enabled.

        Args:
            broker_name: Name of the broker
            selected_portfolio: Selected portfolio filter

        Returns:
            True if broker is enabled, False otherwise
        """
        config = self.get_broker_config(broker_name)
        if not config:
            return False

        # Check if the broker matches the selected portfolio
        if selected_portfolio != PortfolioId.ALL:
            broker_portfolio = PortfolioId.from_id(broker_name)
            if selected_portfolio != broker_portfolio:
                return False

        # Broker-specific enabled logic
        if broker_name == "bitvavo":
            return config.is_enabled() and config is not None and config.credentials is not None
        else:
            return config.is_enabled()

    def is_broker_connected(self, broker_name: str, selected_portfolio: PortfolioId = PortfolioId.ALL) -> bool:
        """
        Check if a broker is connected.

        Args:
            broker_name: Name of the broker
            selected_portfolio: Selected portfolio filter

        Returns:
            True if broker is connected, False otherwise
        """
        config = self.get_broker_config(broker_name)
        if not config:
            return False

        # Check if the broker matches the selected portfolio
        if selected_portfolio != PortfolioId.ALL:
            broker_portfolio = PortfolioId.from_id(broker_name)
            if selected_portfolio != broker_portfolio:
                return False

        # Delegate to broker-specific connection check
        if broker_name == "degiro":
            return self._is_degiro_connected(selected_portfolio)
        elif broker_name == "bitvavo":
            return self._is_bitvavo_connected(selected_portfolio)
        elif broker_name == "ibkr":
            return self._is_ibkr_connected(selected_portfolio)

        return False

    def is_broker_enabled_and_connected(
        self, broker_name: str, selected_portfolio: PortfolioId = PortfolioId.ALL
    ) -> bool:
        """
        Check if a broker is both enabled and connected.

        Args:
            broker_name: Name of the broker
            selected_portfolio: Selected portfolio filter

        Returns:
            True if broker is enabled and connected, False otherwise
        """
        return self.is_broker_enabled(broker_name, selected_portfolio) and self.is_broker_connected(
            broker_name, selected_portfolio
        )

    def _is_degiro_connected(self, selected_portfolio: PortfolioId = PortfolioId.ALL) -> bool:
        """DeGiro-specific connection check."""
        # Lazy import to avoid circular dependency
        from stonks_overwatch.services.brokers.degiro.client.degiro_client import DeGiroService

        config = self.get_broker_config("degiro")
        return (
            DeGiroService().check_connection() or (config is not None and config.credentials is not None)
        ) and selected_portfolio in [PortfolioId.ALL, PortfolioId.DEGIRO]

    def _is_bitvavo_connected(self, selected_portfolio: PortfolioId = PortfolioId.ALL) -> bool:
        """Bitvavo-specific connection check."""
        config = self.get_broker_config("bitvavo")
        return (
            config is not None
            and config.credentials is not None
            and selected_portfolio in [PortfolioId.ALL, PortfolioId.BITVAVO]
        )

    def _is_ibkr_connected(self, selected_portfolio: PortfolioId = PortfolioId.ALL) -> bool:
        """IBKR-specific connection check."""
        config = self.get_broker_config("ibkr")
        return (
            config is not None
            and config.credentials is not None
            and selected_portfolio in [PortfolioId.ALL, PortfolioId.IBKR]
        )


class Config:
    logger = StonksLogger.get_logger("stonks_overwatch.config", "[CONFIG]")

    DEFAULT_BASE_CURRENCY: str = "EUR"

    def __init__(
        self,
        base_currency: Optional[str] = DEFAULT_BASE_CURRENCY,
        degiro_configuration: Optional[DegiroConfig] = None,
        bitvavo_configuration: Optional[BitvavoConfig] = None,
        ibkr_configuration: Optional[IbkrConfig] = None,
    ) -> None:
        if base_currency and not isinstance(base_currency, str):
            raise TypeError("base_currency must be a string")
        self.base_currency = base_currency

        # Instance-based registry
        self.registry = ConfigRegistry()

        # Set broker configurations using the factory
        if degiro_configuration:
            self.registry.set_broker_config("degiro", degiro_configuration)
        if bitvavo_configuration:
            self.registry.set_broker_config("bitvavo", bitvavo_configuration)
        if ibkr_configuration:
            self.registry.set_broker_config("ibkr", ibkr_configuration)

    def is_enabled(self, selected_portfolio: PortfolioId) -> bool:
        """
        Check if any broker is enabled for the selected portfolio.

        Args:
            selected_portfolio: Selected portfolio filter

        Returns:
            True if any broker is enabled, False otherwise
        """
        if selected_portfolio == PortfolioId.ALL:
            return any(
                self.registry.is_broker_enabled(broker_name, selected_portfolio)
                for broker_name in self.registry.get_available_brokers()
            )
        else:
            # Handle case where selected_portfolio might be a string or invalid PortfolioId
            if isinstance(selected_portfolio, str):
                return False
            try:
                broker_name = selected_portfolio.id
                return self.registry.is_broker_enabled(broker_name, selected_portfolio)
            except AttributeError:
                return False

    def is_enabled_and_connected(self, selected_portfolio: PortfolioId) -> bool:
        """
        Check if any broker is enabled and connected for the selected portfolio.
        Args:
            selected_portfolio: Selected portfolio filter

        Returns:
            True if any broker is enabled and connected, False otherwise
        """
        if selected_portfolio == PortfolioId.ALL:
            return any(
                self.registry.is_broker_enabled_and_connected(broker_name, selected_portfolio)
                for broker_name in self.registry.get_available_brokers()
            )
        else:
            # Handle case where selected_portfolio might be a string or invalid PortfolioId
            if isinstance(selected_portfolio, str):
                return False
            try:
                broker_name = selected_portfolio.id
                return self.registry.is_broker_enabled_and_connected(broker_name, selected_portfolio)
            except AttributeError:
                return False

    # Legacy methods for backward compatibility
    def is_degiro_enabled(self, selected_portfolio: PortfolioId = PortfolioId.ALL) -> bool:
        return self.registry.is_broker_enabled("degiro", selected_portfolio)

    def is_degiro_offline(self):
        config = self.registry.get_broker_config("degiro")
        return config.offline_mode if config else False

    def is_degiro_connected(self, selected_portfolio: PortfolioId = PortfolioId.ALL) -> bool:
        return self.registry.is_broker_connected("degiro", selected_portfolio)

    def is_degiro_enabled_and_connected(self, selected_portfolio: PortfolioId = PortfolioId.ALL) -> bool:
        return self.registry.is_broker_enabled_and_connected("degiro", selected_portfolio)

    def is_bitvavo_enabled(self, selected_portfolio: PortfolioId = PortfolioId.ALL) -> bool:
        return self.registry.is_broker_enabled("bitvavo", selected_portfolio)

    def is_ibkr_enabled(self, selected_portfolio: PortfolioId = PortfolioId.ALL) -> bool:
        return self.registry.is_broker_enabled("ibkr", selected_portfolio)

    def __eq__(self, value: object) -> bool:
        if isinstance(value, Config):
            # Compare base currency
            if self.base_currency != value.base_currency:
                return False
            # Compare all registered broker configs by value
            self_brokers = set(self.registry.get_available_brokers())
            other_brokers = set(value.registry.get_available_brokers())
            if self_brokers != other_brokers:
                return False
            for broker in self_brokers:
                if self.registry.get_broker_config(broker) != value.registry.get_broker_config(broker):
                    return False
            return True
        return False

    def __repr__(self) -> str:
        return (
            f"Config(base_currency={self.base_currency}, "
            f"degiro_config={self.registry.get_broker_config('degiro')}, "
            f"bitvavo_config={self.registry.get_broker_config('bitvavo')}, "
            f"ibkr_config={self.registry.get_broker_config('ibkr')}, "
            ")"
        )

    @classmethod
    def from_dict(cls, data: dict) -> "Config":
        base_currency = data.get("base_currency", Config.DEFAULT_BASE_CURRENCY)

        # Use factory to create broker configurations
        degiro_configuration = config_factory.create_broker_config_from_dict(
            "degiro", data.get(DegiroConfig.config_key, {})
        )
        bitvavo_configuration = config_factory.create_broker_config_from_dict(
            "bitvavo", data.get(BitvavoConfig.config_key, {})
        )
        ibkr_configuration = config_factory.create_broker_config_from_dict("ibkr", data.get(IbkrConfig.config_key, {}))

        return cls(base_currency, degiro_configuration, bitvavo_configuration, ibkr_configuration)

    @classmethod
    def from_json_file(cls, file_path: str | Path) -> "Config":
        """Loads the configuration from a JSON file."""
        data = {}
        with open(file_path, "r") as f:
            data = json.load(f)
        return cls.from_dict(data)

    @classmethod
    def _default(cls) -> "Config":
        """
        Create a fresh default configuration instance.

        This is an internal method used by GlobalConfig and tests.
        For production code, use Config.get_global() for cached access.

        Returns:
            A fresh configuration instance with default values
        """
        return Config(
            base_currency=Config.DEFAULT_BASE_CURRENCY,
            degiro_configuration=config_factory.create_default_broker_config("degiro"),
            bitvavo_configuration=config_factory.create_default_broker_config("bitvavo"),
            ibkr_configuration=config_factory.create_default_broker_config("ibkr"),
        )

    @classmethod
    def get_global(cls) -> "Config":
        """
        Get the global configuration instance using cached access.

        This method provides cached access to the configuration,
        reducing redundant configuration creation and logging.

        Returns:
            The global configuration instance
        """
        from stonks_overwatch.config.global_config import global_config

        return global_config.get_config()
