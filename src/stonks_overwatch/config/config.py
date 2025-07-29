import json
from pathlib import Path
from typing import Dict, Optional, Set, Type

from stonks_overwatch.config.base_config import BaseConfig
from stonks_overwatch.config.bitvavo import BitvavoConfig
from stonks_overwatch.config.degiro import DegiroConfig
from stonks_overwatch.config.ibkr import IbkrConfig
from stonks_overwatch.core.factories.broker_factory import BrokerFactory
from stonks_overwatch.services.models import PortfolioId
from stonks_overwatch.utils.core.logger import StonksLogger


def _ensure_unified_registry_initialized():
    """
    Lazy initialization of unified registry to avoid circular imports.

    This function imports and initializes the unified registry only when needed,
    avoiding circular import issues during module loading.
    """
    try:
        from stonks_overwatch.core.registry_setup import ensure_unified_registry_initialized

        ensure_unified_registry_initialized()
    except ImportError as e:
        # Log warning but don't fail - fall back to legacy behavior
        StonksLogger.get_logger("stonks_overwatch.config", "[CONFIG]").debug(
            f"Could not initialize unified registry due to import error: {e}"
        )
    except Exception as e:
        # Log warning but don't fail - fall back to legacy behavior
        StonksLogger.get_logger("stonks_overwatch.config", "[CONFIG]").debug(
            f"Could not initialize unified registry: {e}"
        )


class ConfigRegistry:
    """
    Registry for managing broker configurations dynamically.

    This class maintains a registry of broker configurations
    and provides a centralized way to manage them.

    **Updated to use BrokerFactory for configuration access.**
    """

    logger = StonksLogger.get_logger("stonks_overwatch.config", "[CONFIG_REGISTRY]")

    def __init__(self, use_broker_factory: bool = True):
        """
        Initialize configuration registry.

        Args:
            use_broker_factory: Whether to use the new BrokerFactory.
                When True, uses the new unified architecture.
                When False, falls back to legacy patterns.
        """
        self._broker_configs: Dict[str, BaseConfig] = {}
        self._broker_config_classes: Dict[str, Type[BaseConfig]] = {}
        self._use_broker_factory = use_broker_factory
        self._factory = None

        if self._use_broker_factory:
            # Initialize with unified broker factory
            try:
                self._factory = BrokerFactory()
            except Exception as e:
                StonksLogger.get_logger("stonks_overwatch.config").warning(f"Failed to initialize BrokerFactory: {e}")

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
        Get broker configuration with fallback.

        Args:
            broker_name: Name of the broker

        Returns:
            Broker configuration instance or None
        """
        # First check if a specific configuration was manually set
        if broker_name in self._broker_configs:
            return self._broker_configs[broker_name]

        # Fallback to factory for default configurations
        if self._use_broker_factory and self._factory:
            config = self._factory.create_default_config(broker_name)
            if config:
                return config

        return None

    def get_available_brokers(self) -> Set[str]:
        """
        Get set of all available broker names.

        Returns:
            Set of broker names that have configurations available
        """
        brokers = set(self._broker_configs.keys())

        if self._use_broker_factory and self._factory:
            # Include brokers from unified factory
            broker_brokers = set(self._factory.get_available_brokers())
            brokers.update(broker_brokers)

        return brokers

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
            self.logger.debug(f"Broker '{broker_name}' is not registered or has no configuration.")
            return False

        # Check if the broker matches the selected portfolio
        if selected_portfolio != PortfolioId.ALL:
            broker_portfolio = PortfolioId.from_id(broker_name)
            if selected_portfolio != broker_portfolio:
                return False

        # Use broker-specific enabled logic (maintains backward compatibility)
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
    """
    Main configuration class that provides access to all broker configurations.

    This class serves as the central configuration manager for the application,
    providing access to broker-specific configurations while maintaining
    backward compatibility.
    """

    logger = StonksLogger.get_logger("stonks_overwatch.config", "[CONFIG]")

    DEFAULT_BASE_CURRENCY: str = "EUR"

    def __init__(
        self,
        base_currency: Optional[str] = DEFAULT_BASE_CURRENCY,
        degiro_configuration: Optional[DegiroConfig] = None,
        bitvavo_configuration: Optional[BitvavoConfig] = None,
        ibkr_configuration: Optional[IbkrConfig] = None,
        use_broker_factory: bool = True,
    ) -> None:
        """
        Initialize configuration with broker-specific settings.

        Args:
            base_currency: The base currency for calculations
            degiro_configuration: DeGiro broker configuration
            bitvavo_configuration: Bitvavo broker configuration
            ibkr_configuration: IBKR broker configuration
            use_broker_factory: Whether to use the new BrokerFactory
                               for additional functionality and consistency
        """
        if base_currency and not isinstance(base_currency, str):
            raise TypeError("base_currency must be a string")

        self.base_currency = base_currency or self.DEFAULT_BASE_CURRENCY
        self.registry = ConfigRegistry(use_broker_factory=use_broker_factory)
        self._use_broker_factory = use_broker_factory
        self._factory = None

        if self._use_broker_factory:
            # Initialize broker factory for enhanced functionality
            try:
                self._factory = BrokerFactory()
            except Exception as e:
                StonksLogger.get_logger("stonks_overwatch.config").warning(f"Failed to initialize BrokerFactory: {e}")

        # Set configurations if provided
        if degiro_configuration:
            self.registry.set_broker_config("degiro", degiro_configuration)

        if bitvavo_configuration:
            self.registry.set_broker_config("bitvavo", bitvavo_configuration)

        if ibkr_configuration:
            self.registry.set_broker_config("ibkr", ibkr_configuration)

    def get_broker_config(self, broker_name: str) -> Optional[BaseConfig]:
        """
        Get a broker configuration.

        Args:
            broker_name: Name of the broker

        Returns:
            Configuration instance if available, None otherwise
        """
        return self.registry.get_broker_config(broker_name)

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
        """Legacy method for backward compatibility."""
        return self.registry.is_broker_enabled("degiro", selected_portfolio)

    def is_bitvavo_enabled(self, selected_portfolio: PortfolioId = PortfolioId.ALL) -> bool:
        """Legacy method for backward compatibility."""
        return self.registry.is_broker_enabled("bitvavo", selected_portfolio)

    def is_ibkr_enabled(self, selected_portfolio: PortfolioId = PortfolioId.ALL) -> bool:
        """Legacy method for backward compatibility."""
        return self.registry.is_broker_enabled("ibkr", selected_portfolio)

    # Additional legacy methods for backward compatibility
    def is_degiro_offline(self) -> bool:
        """Legacy method for backward compatibility."""
        config = self.registry.get_broker_config("degiro")
        return config.offline_mode if config else False

    def is_degiro_connected(self, selected_portfolio: PortfolioId = PortfolioId.ALL) -> bool:
        """Legacy method for backward compatibility."""
        return self.registry.is_broker_connected("degiro", selected_portfolio)

    def is_degiro_enabled_and_connected(self, selected_portfolio: PortfolioId = PortfolioId.ALL) -> bool:
        """Legacy method for backward compatibility."""
        return self.registry.is_broker_enabled_and_connected("degiro", selected_portfolio)

    def is_bitvavo_offline(self) -> bool:
        """Legacy method for backward compatibility."""
        config = self.registry.get_broker_config("bitvavo")
        return config.offline_mode if config else False

    def __eq__(self, value: object) -> bool:
        if isinstance(value, Config):
            if self.base_currency != value.base_currency:
                return False
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
    def from_dict(cls, data: dict, use_broker_factory: bool = True) -> "Config":
        """
        Create configuration from dictionary data.

        Args:
            data: Dictionary containing configuration data
            use_broker_factory: Whether to use the new BrokerFactory

        Returns:
            Config instance created from the data
        """
        base_currency = data.get("base_currency", cls.DEFAULT_BASE_CURRENCY)

        broker_factory = BrokerFactory()
        degiro_configuration = broker_factory.create_config_from_dict("degiro", data.get(DegiroConfig.config_key, {}))
        bitvavo_configuration = broker_factory.create_config_from_dict(
            "bitvavo", data.get(BitvavoConfig.config_key, {})
        )
        ibkr_configuration = broker_factory.create_config_from_dict("ibkr", data.get(IbkrConfig.config_key, {}))

        return cls(base_currency, degiro_configuration, bitvavo_configuration, ibkr_configuration)

    @classmethod
    def from_json_file(cls, file_path: str | Path, use_broker_factory: bool = True) -> "Config":
        """
        Create configuration from JSON file.

        Args:
            file_path: Path to the JSON configuration file
            use_broker_factory: Whether to use the new BrokerFactory

        Returns:
            Config instance loaded from the file
        """
        with open(file_path, "r") as f:
            data = json.load(f)

        return cls.from_dict(data, use_broker_factory)

    @classmethod
    def _default(cls, use_broker_factory: bool = True) -> "Config":
        """
        Create default configuration with all brokers initialized to defaults.

        This method creates a Config instance with default configurations
        for all supported brokers using the BrokerFactory.

        Args:
            use_broker_factory: Whether to use the new BrokerFactory

        Returns:
            Config instance with default broker configurations
        """
        broker_factory = BrokerFactory()

        return cls(
            degiro_configuration=broker_factory.create_default_config("degiro"),
            bitvavo_configuration=broker_factory.create_default_config("bitvavo"),
            ibkr_configuration=broker_factory.create_default_config("ibkr"),
            use_broker_factory=True,
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
