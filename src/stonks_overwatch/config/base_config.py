import json
import os
from abc import ABC, abstractmethod
from datetime import date
from pathlib import Path
from typing import Any, Dict, Optional, Type, TypeVar, cast

from stonks_overwatch.config.base_credentials import BaseCredentials
from stonks_overwatch.settings import PROJECT_PATH
from stonks_overwatch.utils.core.logger import StonksLogger
from stonks_overwatch.utils.core.logger_constants import LOGGER_CONFIG, TAG_BASE_CONFIG


class BaseConfig(ABC):
    logger = StonksLogger.get_logger(LOGGER_CONFIG, TAG_BASE_CONFIG)
    CONFIG_PATH = os.path.join(PROJECT_PATH, "config", "config.json")
    DEFAULT_UPDATE_FREQUENCY = 5

    def __init__(
        self,
        credentials: Optional[BaseCredentials],
        start_date: date,
        enabled: bool = False,
        offline_mode: bool = False,
        update_frequency_minutes: int = DEFAULT_UPDATE_FREQUENCY,
    ) -> None:
        if update_frequency_minutes < 1:
            raise ValueError("Update frequency must be at least 1 minute")

        self.enabled = enabled
        self.credentials = credentials
        self.start_date = start_date
        self.update_frequency_minutes = update_frequency_minutes
        self.offline_mode = offline_mode

    def __eq__(self, value: object) -> bool:
        if isinstance(value, self.__class__):
            return (
                self.is_enabled() == value.is_enabled()
                and self.credentials == value.credentials
                and self.offline_mode == value.offline_mode
                and self.start_date == value.start_date
                and self.update_frequency_minutes == value.update_frequency_minutes
            )
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
    @abstractmethod
    def from_dict(cls, data: Dict[str, Any]) -> "BaseConfig":
        """Create config instance from dictionary data."""
        pass

    # Note: config_key should be defined as a class attribute in subclasses
    # e.g., config_key = "broker_name"

    @classmethod
    def load_config(cls, broker_name: str, json_override_path: str | Path = None) -> "BaseConfig":
        """
        Loads configuration from database with optional JSON file override.

        This method first loads configuration from the database model,
        then applies any overrides found in the JSON configuration file.

        Args:
            broker_name: Name of the broker to load configuration for
            json_override_path: Path to JSON configuration file (for overrides, defaults to CONFIG_PATH)

        Returns:
            BaseConfig instance with merged configuration
        """
        if json_override_path is None:
            json_override_path = cls.CONFIG_PATH

        from stonks_overwatch.services.brokers.models import BrokersConfiguration

        # Get DB configuration using synchronous Django ORM
        db_config_data = {}
        try:
            # Use Django's synchronous ORM directly - much simpler and more reliable
            try:
                db_result = BrokersConfiguration.objects.get(broker_name=broker_name)
            except BrokersConfiguration.DoesNotExist:
                db_result = None

            if db_result:
                db_config_data = cls._convert_db_model_to_dict(db_result)

        except Exception as e:
            cls.logger.warning(f"Failed to load configuration from database for {broker_name}: {e}")
            # Continue with empty DB config if DB fails

        # Get JSON configuration if file exists
        json_config_data = {}
        if os.path.exists(json_override_path):
            try:
                with open(json_override_path, "r") as f:
                    json_data = json.load(f)
                    json_config_data = json_data.get(cls.config_key, {})
                cls.logger.debug(f"Loaded JSON override configuration for {broker_name}")
            except Exception as e:
                cls.logger.warning(f"Failed to load JSON configuration for {broker_name}: {e}")

        # Merge configurations: DB first, then JSON overrides
        merged_config = cls._merge_config_data(db_config_data, json_config_data)

        return cls.from_dict(merged_config)

    @classmethod
    def from_db_with_json_override(cls, broker_name: str) -> "LazyConfig":
        """
        Loads configuration from database with optional JSON file override using lazy loading.

        This method returns a lazy-loading wrapper that defers database access
        until the configuration is actually needed. This prevents database access
        during Django app initialization.

        Args:
            broker_name: Name of the broker to load configuration for

        Returns:
            LazyConfig wrapper that loads actual configuration when accessed
        """
        return LazyConfig(cls, broker_name)

    @classmethod
    def from_json_file(cls, file_path: str | Path) -> "BaseConfig":
        """
        Loads configuration from JSON file only (legacy method).

        This method only reads from the JSON file without database integration.
        Use from_db_with_json_override instead for production code.

        Args:
            file_path: Path to JSON configuration file

        Returns:
            BaseConfig instance from JSON data only
        """
        data = {}
        with open(file_path, "r") as f:
            data = json.load(f)
        return cls.from_dict(data.get(cls.config_key, {}))

    @classmethod
    def _convert_db_model_to_dict(cls, db_model) -> Dict[str, Any]:
        """
        Convert database model to configuration dictionary format.

        Args:
            db_model: BrokersConfiguration database model instance

        Returns:
            Dictionary in format expected by from_dict method
        """
        if not db_model:
            return {}

        return {
            "enabled": db_model.enabled,
            "credentials": db_model.credentials or {},
            "start_date": db_model.start_date.isoformat() if db_model.start_date else None,
            "update_frequency_minutes": db_model.update_frequency,
        }

    @classmethod
    def _merge_config_data(cls, db_data: Dict[str, Any], json_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Merge database and JSON configuration data with JSON taking precedence.

        Priority order (highest to lowest):
        1. JSON file configuration (config.json) - Takes precedence for overrides
        2. Database configuration - Used as base when JSON doesn't specify a value

        This allows config.json to override database defaults, which is useful for:
        - Development/testing environments
        - Temporary configuration changes
        - Environment-specific overrides

        Args:
            db_data: Configuration data from database (base defaults)
            json_data: Configuration data from JSON file (overrides)

        Returns:
            Merged configuration dictionary
        """
        # Start with DB data as base
        merged = db_data.copy()

        # Override with JSON data (JSON has priority for overrides)
        for key, value in json_data.items():
            if key == "credentials" and isinstance(value, dict) and isinstance(merged.get(key), dict):
                # Merge credentials dictionaries (JSON credentials override DB)
                merged_credentials = merged.get(key, {}).copy()
                merged_credentials.update(value)
                merged[key] = merged_credentials
            else:
                # Direct override for other fields (JSON value wins)
                merged[key] = value

        return merged


class LazyConfig(BaseConfig):
    """
    Lazy-loading configuration wrapper that defers database access until needed.

    This prevents database access during Django app initialization while providing
    a transparent interface to the actual configuration.
    """

    # noinspection PyMissingConstructor
    def __init__(self, config_class, broker_name: str):
        """
        Initialize lazy config wrapper.

        Args:
            config_class: The actual configuration class to instantiate
            broker_name: Name of the broker for loading configuration
        """
        # Don't call super().__init__ to avoid requiring credentials immediately
        self._config_class = config_class
        self._broker_name = broker_name
        self._loaded_config = None
        self._is_loaded = False

    def _ensure_loaded(self):
        """Load the actual configuration if not already loaded."""
        if not self._is_loaded:
            self._loaded_config = self._config_class.load_config(self._broker_name)
            self._is_loaded = True

    def __getattr__(self, name):
        """Proxy any attribute access to the loaded configuration."""
        self._ensure_loaded()
        return getattr(self._loaded_config, name)

    @property
    def get_credentials(self):
        """Proxy credentials access to loaded configuration."""
        self._ensure_loaded()
        return self._loaded_config.get_credentials

    def get_loaded_config(self):
        """
        Get the actual loaded configuration instance.

        This method provides a public interface to access the underlying
        configuration without exposing protected members.

        Returns:
            The actual configuration instance after ensuring it's loaded
        """
        self._ensure_loaded()
        return self._loaded_config

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "BaseConfig":
        """LazyConfig doesn't support direct construction from dict."""
        raise NotImplementedError("LazyConfig doesn't support from_dict. Use from_db_with_json_override instead.")

    def __eq__(self, other):
        """Compare LazyConfig instances."""
        if not isinstance(other, LazyConfig):
            # Compare with loaded config if other is a BaseConfig
            if isinstance(other, BaseConfig):
                self._ensure_loaded()
                return self._loaded_config == other
            return False

        # Both are LazyConfig - compare class and broker name
        if self._config_class != other._config_class or self._broker_name != other._broker_name:
            return False

        # If both are loaded, compare loaded configs
        if self._is_loaded and other._is_loaded:
            return self._loaded_config == other._loaded_config

        # If neither is loaded, they're equal if class and broker match
        return not self._is_loaded and not other._is_loaded

    def __repr__(self):
        if self._is_loaded:
            return f"LazyConfig(loaded={self._loaded_config})"
        else:
            return f"LazyConfig(class={self._config_class.__name__}, broker={self._broker_name}, not_loaded=True)"


# Configuration resolution utilities

# Type variable for configuration classes
ConfigType = TypeVar("ConfigType", bound=BaseConfig)


def resolve_config(config: BaseConfig, expected_type: Type[ConfigType]) -> ConfigType:
    """
    Resolve a configuration instance that may be wrapped in LazyConfig.

    This function handles both LazyConfig wrapper instances and direct config instances,
    ensuring the returned configuration is of the expected type.

    Args:
        config: Configuration instance that may be a LazyConfig wrapper
        expected_type: Expected configuration class type

    Returns:
        Resolved configuration instance of the expected type

    Raises:
        TypeError: If the resolved configuration is not of the expected type
    """
    if isinstance(config, LazyConfig):
        # Use the public method to get the loaded configuration
        actual_config = config.get_loaded_config()
        if not isinstance(actual_config, expected_type):
            raise TypeError(f"Expected {expected_type.__name__}, got {type(actual_config).__name__}")
        return cast(ConfigType, actual_config)
    elif isinstance(config, expected_type):
        return cast(ConfigType, config)
    else:
        raise TypeError(f"Expected {expected_type.__name__} or LazyConfig, got {type(config).__name__}")


def resolve_config_from_factory(broker_name: str, expected_type: Type[ConfigType]) -> ConfigType:
    """
    Create and resolve a configuration from BrokerFactory.

    This is a convenience function that combines broker factory usage with
    configuration resolution, handling the common pattern used in broker clients.

    Args:
        broker_name: Name of the broker to create configuration for
        expected_type: Expected configuration class type

    Returns:
        Resolved configuration instance of the expected type

    Raises:
        ImportError: If BrokerFactory cannot be imported
        TypeError: If the resolved configuration is not of the expected type
        RuntimeError: If configuration creation fails
    """
    try:
        from stonks_overwatch.core.factories.broker_factory import BrokerFactory

        broker_factory = BrokerFactory()
        config = broker_factory.create_config(broker_name)

        if config is None:
            raise RuntimeError(
                f"{expected_type.__name__} configuration not available. This usually means:\n"
                f"1. The broker registry hasn't been initialized (call django.setup() for scripts)\n"
                f"2. {broker_name.title()} broker registration is missing from registry setup\n"
                f"3. No valid {broker_name.title()} configuration file exists\n"
                "Please ensure Django is properly initialized before using broker services."
            )

        return resolve_config(config, expected_type)

    except ImportError as e:
        raise ImportError(f"Failed to import BrokerFactory: {e}") from e
