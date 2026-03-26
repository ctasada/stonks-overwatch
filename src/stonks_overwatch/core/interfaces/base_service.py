"""
Base service interface with dependency injection support.

This module provides a base interface that supports dependency injection
of configuration while maintaining backward compatibility with existing
service implementations.
"""

from typing import Optional

from stonks_overwatch.config.base_config import BaseConfig


class DependencyInjectionMixin:
    """
    Mixin that provides dependency injection capabilities for services.

    This mixin allows services to receive configuration via dependency injection
    while maintaining backward compatibility with existing code that doesn't use
    the unified factory.
    """

    def __init__(self, config: Optional[BaseConfig] = None, *args, **kwargs):
        """
        Initialize the service with optional configuration dependency injection.

        Args:
            config: Optional broker-specific configuration. If not provided,
                   will fall back to global configuration access.
            *args: Additional positional arguments for service constructors
            **kwargs: Additional keyword arguments for service constructors
        """
        super().__init__(*args, **kwargs)
        self._injected_config = config
        self._global_config = None

    def _ensure_global_config(self) -> None:
        """Lazily initialise _global_config, avoiding circular imports at module load time."""
        if self._global_config is None:
            from stonks_overwatch.config.config import Config

            self._global_config = Config.get_global()

    @property
    def config(self) -> BaseConfig:
        """
        Get the service configuration.

        Returns configuration in the following priority:
        1. Injected configuration (from dependency injection)
        2. Global configuration (backward compatibility)

        Returns:
            BaseConfig: The configuration instance to use
        """
        if self._injected_config is not None:
            return self._injected_config

        self._ensure_global_config()
        return self._global_config

    @property
    def base_currency(self) -> str:
        """
        Get the base currency from configuration.

        Returns:
            str: The base currency (e.g., 'EUR', 'USD')
        """
        if self._injected_config is not None:
            if hasattr(self._injected_config, "base_currency"):
                base_currency = self._injected_config.base_currency
                # If base_currency is None, fall back to global config
                # But if it's an empty string, that's a valid value to return
                if base_currency is not None:
                    return base_currency

        self._ensure_global_config()
        return self._global_config.base_currency

    def is_dependency_injection_enabled(self) -> bool:
        """
        Check if dependency injection is being used.

        Returns:
            bool: True if configuration was injected, False if using global config
        """
        return self._injected_config is not None


class BaseService(DependencyInjectionMixin):
    """
    Base service class that all broker services can inherit from.

    This provides a standard foundation for services with dependency injection
    support while maintaining backward compatibility.
    """

    def __init__(self, config: Optional[BaseConfig] = None, *args, **kwargs):
        """
        Initialize the base service.

        Args:
            config: Optional broker-specific configuration
            *args: Additional positional arguments
            **kwargs: Additional keyword arguments
        """
        super().__init__(config, *args, **kwargs)
