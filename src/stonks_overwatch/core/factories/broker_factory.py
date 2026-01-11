"""
Broker factory for creating both configurations and services.

This module provides a unified factory that handles both broker configuration
and service creation in a single interface with automatic dependency injection,
eliminating the need for separate factory systems.
"""

from typing import Any, Dict, Optional

from stonks_overwatch.config.base_config import BaseConfig
from stonks_overwatch.core.exceptions import ServiceFactoryException
from stonks_overwatch.core.factories.broker_registry import (
    BrokerRegistry,
)
from stonks_overwatch.core.interfaces.authentication_service import AuthenticationServiceInterface
from stonks_overwatch.core.interfaces.deposit_service import DepositServiceInterface
from stonks_overwatch.core.interfaces.dividend_service import DividendServiceInterface
from stonks_overwatch.core.interfaces.portfolio_service import PortfolioServiceInterface
from stonks_overwatch.core.interfaces.transaction_service import TransactionServiceInterface
from stonks_overwatch.core.service_types import ServiceType
from stonks_overwatch.utils.core.logger import StonksLogger
from stonks_overwatch.utils.core.singleton import singleton


class BrokerFactoryError(ServiceFactoryException):
    """Exception raised for broker factory errors."""

    pass


@singleton
class BrokerFactory:
    """
    Unified factory for creating both configurations and services with dependency injection.

    This singleton factory uses the broker registry to create instances of both
    broker configurations and services, with automatic dependency injection of
    configurations into services.
    """

    def __init__(self):
        """
        Initialize the broker factory.

        Sets up the factory with access to the broker registry and initializes
        caching systems for both configurations and services.
        """
        self.logger = StonksLogger.get_logger("stonks_overwatch.core", "[BROKER_FACTORY]")
        self._registry = BrokerRegistry()

        # Configuration caching
        self._config_instances: Dict[str, BaseConfig] = {}

        # Service caching - nested dict: broker_name -> service_type -> instance
        self._service_instances: Dict[str, Dict[ServiceType, Any]] = {}

        # Cache control
        self._cache_enabled = True

    # Configuration creation methods
    def create_config(self, broker_name: str, **kwargs) -> Optional[BaseConfig]:
        """
        Create broker configuration instance with caching.

        Args:
            broker_name: Name of the broker
            **kwargs: Arguments to pass to the configuration constructor

        Returns:
            Configuration instance if broker is registered, None otherwise
        """
        # Check cache first - only cache if no custom kwargs (default config)
        if self._cache_enabled and not kwargs and broker_name in self._config_instances:
            return self._config_instances[broker_name]

        config_class = self._registry.get_config_class(broker_name)
        if not config_class:
            self.logger.warning(f"No configuration class registered for broker: {broker_name}")
            return None

        try:
            # If no custom kwargs provided, try to use new DB+JSON loading method first
            if not kwargs:
                if hasattr(config_class, "from_db_with_json_override"):
                    config = config_class.from_db_with_json_override(broker_name)
                elif hasattr(config_class, "default"):
                    # Fallback to legacy default method
                    config = config_class.default()
            else:
                config = config_class(**kwargs)

            # Cache the instance only if no custom kwargs (default config)
            if self._cache_enabled and not kwargs:
                self._config_instances[broker_name] = config
                self.logger.debug(f"Created and cached configuration for broker: {broker_name}")
            else:
                self.logger.debug(f"Created configuration for broker: {broker_name}")

            return config
        except Exception as e:
            self.logger.error(f"Failed to create configuration for broker {broker_name}: {e}")
            raise BrokerFactoryError(f"Failed to create configuration for broker '{broker_name}': {e}") from e

    def create_default_config(self, broker_name: str) -> Optional[BaseConfig]:
        """
        Create default broker configuration instance.

        Args:
            broker_name: Name of the broker

        Returns:
            Default configuration instance if broker is registered, None otherwise
        """
        config_class = self._registry.get_config_class(broker_name)
        if not config_class:
            self.logger.warning(f"No configuration class registered for broker: {broker_name}")
            return None

        try:
            config = config_class.default()
            self.logger.debug(f"Created default configuration for broker: {broker_name}")
            return config
        except Exception as e:
            self.logger.error(f"Failed to create default configuration for broker {broker_name}: {e}")
            raise BrokerFactoryError(f"Failed to create default configuration for broker '{broker_name}': {e}") from e

    def create_config_from_dict(self, broker_name: str, data: dict) -> Optional[BaseConfig]:
        """
        Create broker configuration instance from dictionary data.

        Args:
            broker_name: Name of the broker
            data: Dictionary containing configuration data

        Returns:
            Configuration instance if broker is registered, None otherwise
        """
        config_class = self._registry.get_config_class(broker_name)
        if not config_class:
            self.logger.warning(f"No configuration class registered for broker: {broker_name}")
            return None

        try:
            config = config_class.from_dict(data)
            self.logger.debug(f"Created configuration from dict for broker: {broker_name}")
            return config
        except Exception as e:
            self.logger.error(f"Failed to create configuration from dict for broker {broker_name}: {e}")
            raise BrokerFactoryError(f"Failed to create configuration from dict for broker '{broker_name}': {e}") from e

    # Service creation methods with dependency injection
    def create_service(self, broker_name: str, service_type: ServiceType, **kwargs) -> Optional[Any]:
        """
        Create service instance with automatic configuration dependency injection.

        Args:
            broker_name: Name of the broker
            service_type: Type of service to create
            **kwargs: Additional arguments to pass to service constructor

        Returns:
            Service instance if available, None otherwise
        """
        # Check cache first
        if (
            self._cache_enabled
            and broker_name in self._service_instances
            and service_type in self._service_instances[broker_name]
        ):
            return self._service_instances[broker_name][service_type]

        service_class = self._registry.get_service_class(broker_name, service_type)
        if not service_class:
            self.logger.warning(f"No {service_type.value} service registered for broker: {broker_name}")
            return None

        try:
            # Automatic dependency injection: inject configuration if not provided
            if "config" not in kwargs:
                config = self.create_config(broker_name)
                if config:
                    kwargs["config"] = config
                    self.logger.debug(f"Injected configuration into {service_type.value} service for {broker_name}")

            # Create service instance
            service = service_class(**kwargs)

            # Cache the instance
            if self._cache_enabled:
                if broker_name not in self._service_instances:
                    self._service_instances[broker_name] = {}
                self._service_instances[broker_name][service_type] = service
                self.logger.debug(f"Created and cached {service_type.value} service for broker: {broker_name}")
            else:
                self.logger.debug(f"Created {service_type.value} service for broker: {broker_name}")

            return service
        except Exception as e:
            self.logger.error(f"Failed to create {service_type.value} service for broker {broker_name}: {e}")
            raise BrokerFactoryError(
                f"Failed to create {service_type.value} service for broker '{broker_name}': {e}"
            ) from e

    # Typed service creation methods
    def create_portfolio_service(self, broker_name: str, **kwargs) -> Optional[PortfolioServiceInterface]:
        """
        Create a portfolio service instance for the specified broker.

        Args:
            broker_name: Name of the broker
            **kwargs: Additional arguments to pass to service constructor

        Returns:
            Portfolio service instance if available, None otherwise
        """
        if not self._registry.broker_supports_service(broker_name, ServiceType.PORTFOLIO):
            raise BrokerFactoryError(f"Broker '{broker_name}' does not support portfolio service")

        return self.create_service(broker_name, ServiceType.PORTFOLIO, **kwargs)

    def create_transaction_service(self, broker_name: str, **kwargs) -> Optional[TransactionServiceInterface]:
        """
        Create a transaction service instance for the specified broker.

        Args:
            broker_name: Name of the broker
            **kwargs: Additional arguments to pass to service constructor

        Returns:
            Transaction service instance if available, None otherwise
        """
        if not self._registry.broker_supports_service(broker_name, ServiceType.TRANSACTION):
            raise BrokerFactoryError(f"Broker '{broker_name}' does not support transaction service")

        return self.create_service(broker_name, ServiceType.TRANSACTION, **kwargs)

    def create_deposit_service(self, broker_name: str, **kwargs) -> Optional[DepositServiceInterface]:
        """
        Create a deposit service instance for the specified broker.

        Args:
            broker_name: Name of the broker
            **kwargs: Additional arguments to pass to service constructor

        Returns:
            Deposit service instance if available, None otherwise
        """
        if not self._registry.broker_supports_service(broker_name, ServiceType.DEPOSIT):
            raise BrokerFactoryError(f"Broker '{broker_name}' does not support deposit service")

        return self.create_service(broker_name, ServiceType.DEPOSIT, **kwargs)

    def create_dividend_service(self, broker_name: str, **kwargs) -> Optional[DividendServiceInterface]:
        """
        Create a dividend service instance for the specified broker.

        Args:
            broker_name: Name of the broker
            **kwargs: Additional arguments to pass to service constructor

        Returns:
            Dividend service instance if supported, None otherwise
        """
        if not self._registry.broker_supports_service(broker_name, ServiceType.DIVIDEND):
            return None

        return self.create_service(broker_name, ServiceType.DIVIDEND, **kwargs)

    def create_fee_service(self, broker_name: str, **kwargs) -> Optional[Any]:
        """
        Create a fee service instance for the specified broker.

        Args:
            broker_name: Name of the broker
            **kwargs: Additional arguments to pass to service constructor

        Returns:
            Fee service instance if supported, None otherwise
        """
        if not self._registry.broker_supports_service(broker_name, ServiceType.FEE):
            return None

        return self.create_service(broker_name, ServiceType.FEE, **kwargs)

    def create_account_service(self, broker_name: str, **kwargs) -> Optional[Any]:
        """
        Create an account service instance for the specified broker.

        Args:
            broker_name: Name of the broker
            **kwargs: Additional arguments to pass to service constructor

        Returns:
            Account service instance if supported, None otherwise
        """
        if not self._registry.broker_supports_service(broker_name, ServiceType.ACCOUNT):
            return None

        return self.create_service(broker_name, ServiceType.ACCOUNT, **kwargs)

    def create_authentication_service(self, broker_name: str, **kwargs) -> Optional[AuthenticationServiceInterface]:
        """
        Create an authentication service instance for the specified broker.

        Args:
            broker_name: Name of the broker
            **kwargs: Additional arguments to pass to service constructor

        Returns:
            Authentication service instance if supported, None otherwise
        """
        if not self._registry.broker_supports_service(broker_name, ServiceType.AUTHENTICATION):
            return None

        return self.create_service(broker_name, ServiceType.AUTHENTICATION, **kwargs)

    # Convenience methods
    def create_all_services(self, broker_name: str, **kwargs) -> Dict[ServiceType, Any]:
        """
        Create all supported services for a broker.

        Args:
            broker_name: Name of the broker
            **kwargs: Additional arguments to pass to service constructors

        Returns:
            Dictionary mapping service types to service instances
        """
        services = {}
        capabilities = self._registry.get_broker_capabilities(broker_name)

        for service_type in capabilities:
            try:
                service = self.create_service(broker_name, service_type, **kwargs)
                if service:
                    services[service_type] = service
            except Exception as e:
                self.logger.warning(f"Failed to create {service_type.value} service for {broker_name}: {e}")

        return services

    def get_available_brokers(self) -> list[str]:
        """
        Get brokers available for both config and services.

        Returns:
            List of broker names with both config and service registrations
        """
        return self._registry.get_fully_registered_brokers()

    def is_broker_available(self, broker_name: str) -> bool:
        """
        Check if a broker is fully available (both config and services registered).

        Args:
            broker_name: Name of the broker

        Returns:
            True if broker is fully available, False otherwise
        """
        return broker_name in self._registry.get_fully_registered_brokers()

    def get_broker_capabilities(self, broker_name: str) -> list[ServiceType]:
        """
        Get the capabilities (service types) of a specific broker.

        Args:
            broker_name: Name of the broker

        Returns:
            List of supported service types
        """
        return self._registry.get_broker_capabilities(broker_name)

    def broker_supports_service(self, broker_name: str, service_type: ServiceType) -> bool:
        """
        Check if a broker supports a specific service type.

        Args:
            broker_name: Name of the broker
            service_type: Type of service to check

        Returns:
            True if broker supports the service, False otherwise
        """
        return self._registry.broker_supports_service(broker_name, service_type)

    # Cache management
    def clear_cache(self, broker_name: Optional[str] = None) -> None:
        """
        Clear cached instances.

        Args:
            broker_name: Optional broker name. If provided, only clears cache for that broker.
                        If None, clears all cached instances.
        """
        if broker_name:
            self._config_instances.pop(broker_name, None)
            self._service_instances.pop(broker_name, None)
            self.logger.debug(f"Cleared cache for broker: {broker_name}")
        else:
            self._config_instances.clear()
            self._service_instances.clear()
            self.logger.debug("Cleared all cached instances")

    def update_broker_credentials(self, broker_name: str, **credentials) -> None:
        """
        Update credentials for a specific broker.

        Args:
            broker_name: Name of the broker to update credentials for
            **credentials: Credential fields to update

        Raises:
            BrokerFactoryError: If the broker is not registered or credential update fails
        """
        config = self.create_config(broker_name)
        if not config:
            raise BrokerFactoryError(f"No configuration found for broker: {broker_name}")

        try:
            # Handle case where no existing credentials exist
            if config.credentials is None:
                # Use a simple mapping for credential classes to avoid complexity
                credential_classes = {
                    "degiro": "stonks_overwatch.config.degiro.DegiroCredentials",
                    "bitvavo": "stonks_overwatch.config.bitvavo.BitvavoCredentials",
                    "ibkr": "stonks_overwatch.config.ibkr.IbkrCredentials",
                }

                credential_class_path = credential_classes.get(broker_name.lower())
                if not credential_class_path:
                    raise BrokerFactoryError(f"No credential class mapping for broker: {broker_name}")

                # Dynamically import the credential class
                module_path, class_name = credential_class_path.rsplit(".", 1)
                module = __import__(module_path, fromlist=[class_name])
                credential_class = getattr(module, class_name)

                # Create new credentials from scratch
                updated_credentials = credential_class(**credentials)
            else:
                # Get the credential class from existing credentials
                credential_class = config.credentials.__class__

                # Merge existing credentials with new ones
                current_credentials_dict = config.credentials.__dict__
                updated_credentials = credential_class(**{**current_credentials_dict, **credentials})

            # Update the configuration
            config.credentials = updated_credentials

            # Clear cache to force refresh on next access
            self.clear_cache(broker_name)

            self.logger.info(f"Updated credentials for broker: {broker_name}")

        except Exception as e:
            self.logger.error(f"Failed to update credentials for broker {broker_name}: {e}")
            raise BrokerFactoryError(f"Failed to update credentials for broker '{broker_name}': {e}") from e

    def update_degiro_credentials(
        self,
        username: str,
        password: str,
        int_account: int = None,
        totp_secret_key: str = None,
        one_time_password: int = None,
    ) -> None:
        """
        Update DeGiro credentials in the configuration.

        This method provides a centralized way to update DeGiro credentials,
        following the Single Responsibility Principle.

        Args:
            username: The username
            password: The password
            int_account: Optional internal account number
            totp_secret_key: Optional TOTP secret key
            one_time_password: Optional one-time password

        Raises:
            BrokerFactoryError: If DeGiro configuration is not found or update fails
        """
        try:
            self.update_broker_credentials(
                "degiro",
                username=username,
                password=password,
                int_account=int_account,
                totp_secret_key=totp_secret_key,
                one_time_password=one_time_password,
            )
            self.logger.info("DeGiro credentials updated successfully")
        except Exception as e:
            self.logger.error(f"Failed to update DeGiro credentials: {e}")
            raise BrokerFactoryError(f"Failed to update DeGiro credentials: {e}") from e

    def disable_caching(self) -> None:
        """
        Disable caching (useful for tests).
        """
        self._cache_enabled = False
        self.clear_cache()
        self.logger.debug("Caching disabled")

    def enable_caching(self) -> None:
        """
        Enable caching (default behavior).
        """
        self._cache_enabled = True
        self.logger.debug("Caching enabled")

    def get_cache_stats(self) -> Dict[str, Any]:
        """
        Get cache statistics for debugging.

        Returns:
            Dictionary with cache statistics
        """
        return {
            "cache_enabled": self._cache_enabled,
            "cached_configs": list(self._config_instances.keys()),
            "cached_services": {broker: list(services.keys()) for broker, services in self._service_instances.items()},
            "total_config_instances": len(self._config_instances),
            "total_service_instances": sum(len(services) for services in self._service_instances.values()),
        }
