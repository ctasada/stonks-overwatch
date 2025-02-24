"""
Configuration factory for dynamic broker configuration management.

This module provides a factory pattern for creating and managing broker configurations
dynamically, eliminating the need for hardcoded broker references in the main Config class.
"""

from typing import Dict, Optional, Type

from stonks_overwatch.config.base_config import BaseConfig
from stonks_overwatch.config.bitvavo import BitvavoConfig
from stonks_overwatch.config.degiro import DegiroConfig
from stonks_overwatch.config.ibkr import IbkrConfig
from stonks_overwatch.utils.core.logger import StonksLogger
from stonks_overwatch.utils.core.singleton import singleton


@singleton
class ConfigFactory:
    """
    Factory for creating and managing broker configurations.

    This singleton class provides a centralized way to register and instantiate
    broker configurations without hardcoding them in the main Config class.
    """

    def __init__(self):
        self.logger = StonksLogger.get_logger("stonks_overwatch.config", "[CONFIG_FACTORY]")
        self._config_classes: Dict[str, Type[BaseConfig]] = {}
        self._default_configs: Dict[str, BaseConfig] = {}  # Cache for default configs
        self._config_cache: Dict[str, BaseConfig] = {}  # Cache for custom configs
        self._cache_enabled = True  # Can be disabled for tests

        # Register default broker configurations
        self._register_default_brokers()

    def _register_default_brokers(self) -> None:
        """Register the default broker configurations."""
        self.register_broker_config("degiro", DegiroConfig)
        self.register_broker_config("bitvavo", BitvavoConfig)
        self.register_broker_config("ibkr", IbkrConfig)

    def register_broker_config(self, broker_name: str, config_class: Type[BaseConfig]) -> None:
        """
        Register a broker configuration class.

        Args:
            broker_name: Name of the broker (e.g., 'degiro', 'bitvavo')
            config_class: Configuration class for the broker
        """
        if not issubclass(config_class, BaseConfig):
            raise ValueError(f"Config class must inherit from BaseConfig: {config_class}")

        self._config_classes[broker_name] = config_class
        self.logger.info(f"Registered broker configuration: {broker_name}")

    def create_broker_config(self, broker_name: str, **kwargs) -> Optional[BaseConfig]:
        """
        Create a broker configuration instance with caching.

        Args:
            broker_name: Name of the broker
            **kwargs: Arguments to pass to the configuration constructor

        Returns:
            Configuration instance if broker is registered, None otherwise
        """
        # Create cache key from kwargs
        cache_key = f"{broker_name}_{hash(frozenset(kwargs.items()))}"

        # Check cache first
        if cache_key in self._config_cache:
            return self._config_cache[cache_key]

        config_class = self._config_classes.get(broker_name)
        if not config_class:
            self.logger.warning(f"Unknown broker configuration: {broker_name}")
            return None

        try:
            config = config_class(**kwargs)
            self._config_cache[cache_key] = config
            self.logger.info(f"Created and cached configuration for broker: {broker_name}")
            return config
        except Exception as e:
            self.logger.error(f"Failed to create configuration for broker {broker_name}: {e}")
            return None

    def create_default_broker_config(self, broker_name: str) -> Optional[BaseConfig]:
        """
        Create or retrieve cached default broker configuration.

        Args:
            broker_name: Name of the broker

        Returns:
            Cached default configuration instance if broker is registered, None otherwise
        """
        # Check cache first if caching is enabled
        if self._cache_enabled and broker_name in self._default_configs:
            return self._default_configs[broker_name]

        config_class = self._config_classes.get(broker_name)
        if not config_class:
            self.logger.warning(f"Unknown broker configuration: {broker_name}")
            return None

        try:
            # Create default config
            config = config_class.default()

            # Cache if enabled
            if self._cache_enabled:
                self._default_configs[broker_name] = config
                self.logger.info(f"Created and cached default configuration for broker: {broker_name}")
            else:
                self.logger.info(f"Created default configuration for broker: {broker_name}")

            return config
        except Exception as e:
            self.logger.error(f"Failed to create default configuration for broker {broker_name}: {e}")
            return None

    def create_broker_config_from_dict(self, broker_name: str, data: dict) -> Optional[BaseConfig]:
        """
        Create a broker configuration instance from a dictionary.

        Args:
            broker_name: Name of the broker
            data: Dictionary containing configuration data

        Returns:
            Configuration instance if broker is registered, None otherwise
        """
        config_class = self._config_classes.get(broker_name)
        if not config_class:
            self.logger.warning(f"Unknown broker configuration: {broker_name}")
            return None

        try:
            config = config_class.from_dict(data)
            self.logger.info(f"Created configuration from dict for broker: {broker_name}")
            return config
        except Exception as e:
            self.logger.error(f"Failed to create configuration from dict for broker {broker_name}: {e}")
            return None

    def get_registered_brokers(self) -> list[str]:
        """
        Get the list of all registered broker names.

        Returns:
            List of registered broker names
        """
        return list(self._config_classes.keys())

    def is_broker_registered(self, broker_name: str) -> bool:
        """
        Check if a broker is registered.

        Args:
            broker_name: Name of the broker

        Returns:
            True if broker is registered, False otherwise
        """
        return broker_name in self._config_classes

    def get_config_class(self, broker_name: str) -> Optional[Type[BaseConfig]]:
        """
        Get the configuration class for a broker.

        Args:
            broker_name: Name of the broker

        Returns:
            Configuration class if broker is registered, None otherwise
        """
        return self._config_classes.get(broker_name)

    def unregister_broker_config(self, broker_name: str) -> None:
        """
        Unregister a broker configuration.

        Args:
            broker_name: Name of the broker to unregister
        """
        if broker_name in self._config_classes:
            del self._config_classes[broker_name]
            self.logger.info(f"Unregistered broker configuration: {broker_name}")
        else:
            self.logger.warning(f"Broker configuration not found for unregistration: {broker_name}")

    def clear_cache(self, broker_name: Optional[str] = None) -> None:
        """
        Clear configuration cache.

        Args:
            broker_name: Optional broker name. If provided, only clears cache for that broker.
                        If None, clears all cached configurations.
        """
        if broker_name:
            self._default_configs.pop(broker_name, None)
            # Clear custom configs for this broker
            keys_to_remove = [k for k in self._config_cache.keys() if k.startswith(f"{broker_name}_")]
            for key in keys_to_remove:
                del self._config_cache[key]
            self.logger.info(f"Cleared cache for broker: {broker_name}")
        else:
            self._default_configs.clear()
            self._config_cache.clear()
            self.logger.info("Cleared all configuration cache")

    def refresh_default_config(self, broker_name: str) -> Optional[BaseConfig]:
        """
        Force refresh of default configuration (useful for runtime config changes).

        Args:
            broker_name: Name of the broker

        Returns:
            Fresh default configuration instance
        """
        # Remove from cache
        self._default_configs.pop(broker_name, None)

        # Create fresh instance
        return self.create_default_broker_config(broker_name)

    def disable_caching(self) -> None:
        """
        Disable caching (useful for tests).
        """
        self._cache_enabled = False
        self._default_configs.clear()
        self._config_cache.clear()
        self.logger.info("Configuration caching disabled")

    def enable_caching(self) -> None:
        """
        Enable caching (default behavior).
        """
        self._cache_enabled = True
        self.logger.info("Configuration caching enabled")


# Global factory instance
config_factory = ConfigFactory()
