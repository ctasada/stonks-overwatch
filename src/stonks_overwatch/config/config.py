import json
from pathlib import Path
from typing import Optional

from stonks_overwatch.config.base_config import BaseConfig
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
        from stonks_overwatch.core.registry_setup import ensure_registry_initialized

        ensure_registry_initialized()
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


class Config:
    """
    Main configuration class that provides access to all broker configurations.

    This class serves as the central configuration manager for the application,
    using the unified BrokerFactory for all broker operations.
    """

    logger = StonksLogger.get_logger("stonks_overwatch.config", "[CONFIG]")

    DEFAULT_BASE_CURRENCY: str = "EUR"

    def __init__(self, base_currency: Optional[str] = DEFAULT_BASE_CURRENCY) -> None:
        """
        Initialize configuration with base currency.

        Args:
            base_currency: The base currency for calculations
        """
        if base_currency and not isinstance(base_currency, str):
            raise TypeError("base_currency must be a string")

        self.base_currency = base_currency or self.DEFAULT_BASE_CURRENCY
        self._factory = BrokerFactory()

    def get_broker_config(self, broker_name: str) -> Optional[BaseConfig]:
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
            return any(
                self._is_broker_enabled(broker_name, selected_portfolio)
                for broker_name in self._factory.get_available_brokers()
            )
        else:
            # Handle case where selected_portfolio might be a string or invalid PortfolioId
            if isinstance(selected_portfolio, str):
                return False
            try:
                broker_name = selected_portfolio.id
                return self._is_broker_enabled(broker_name, selected_portfolio)
            except AttributeError:
                return False

    def _is_broker_enabled(self, broker_name: str, selected_portfolio: PortfolioId = PortfolioId.ALL) -> bool:
        """
        Check if a specific broker is enabled for the selected portfolio.

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

        return config.is_enabled()

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
        return (
            f"Config(base_currency={self.base_currency}, "
            f"degiro_config={self.get_broker_config('degiro')}, "
            f"bitvavo_config={self.get_broker_config('bitvavo')}, "
            f"ibkr_config={self.get_broker_config('ibkr')}, "
            ")"
        )

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
        from stonks_overwatch.config.global_config import global_config

        return global_config.get_config()
